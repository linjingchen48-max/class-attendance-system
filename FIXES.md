# 本次修复说明

## 1. SQL 中的 `%` 字面量导致列表页与编辑页不可用

**现象**：后台考勤列表接口返回 `读取数据失败：unsupported format character 'Y'`，
编辑页直接 HTTP 500。

**原因**：PyMySQL 的 `cursor.execute(query, args)` 内部执行 `query % escaped_args`，
是 Python 的 `%` 格式化。SQL 里的 `DATE_FORMAT(\`date\`, '%Y-%m-%d')` 中，
`%Y` 被当作格式符解析。

**修改**：`models/AttendanceModel.py` 中 `list_all()`、`get_by_id()` 的
`'%Y-%m-%d'` 改为 `'%%Y-%%m-%%d'`（2 处）。
`stats()` 不含 `%` 字面量，原本就不受影响。

## 2. 根因：`params or ()` 让不带参数的查询也走格式化

**原写法**：`models/database.py` 中 `cur.execute(sql, params or ())`。

`None` 被转成空元组 `()`，而 PyMySQL 只在 `args is None` 时才跳过格式化，
空元组仍会触发 `query % ()`。这意味着**任何**含 `%` 的 SQL（`DATE_FORMAT`、
`LIKE '%张%'` 等）即使不传参数也会报错，只是错误类型变成
`TypeError: not enough arguments for format string`。

**修改**：改为 `cur.execute(sql, params)`，`None` 原样传入。

## 3. 口令由明文改为 PBKDF2 摘要

**原写法**：`teacher.password` 存明文，
`WHERE username=%s AND password=%s` 直接比对。

**修改**：
- `models/TeacherModel.py`：按用户名取行后用
  `werkzeug.security.check_password_hash` 校验；`create()` 写入时先
  `generate_password_hash`；新增 `set_password()`。
- `schema.sql`：`password` 字段加注释说明存摘要；演示账号写入
  `admin123` 的 PBKDF2 摘要（账号口令不变，仍是 admin / admin123）。
- `requirements.txt`：显式声明 `Werkzeug>=2.2`。
- 新增 `tools/set_password.py`，用法：`python tools/set_password.py admin 新口令`。

**已有数据库的迁移**：若库里还是明文行，执行
`python tools/set_password.py admin admin123` 重写为摘要即可。

## 验证

两级验证：

1. `smoke_test.py` —— 以与 PyMySQL 相同的 `%` 格式化逻辑替换数据库层，
   不依赖真实数据库即可运行。
2. 真实 MySQL + 真实 PyMySQL 的端到端对照 —— 原始代码配原始 schema，
   修复后配新 schema，跑同一套断言。

端到端结果：

| 用例 | 原始代码 | 修复后 |
| --- | --- | --- |
| admin/admin123 登录 | ✓ | ✓ |
| 错误口令被拒 | ✓ | ✓ |
| 考勤列表 API | ✗ `unsupported format character 'Y'` | ✓ 返回 15 条 |
| 编辑页 `get_by_id` | ✗ HTTP 500 | ✓ HTTP 200 |
| 大屏统计 API | ✓ | ✓ |
| SQL 中无明文口令 | ✗ | ✓ |

即：原始版本的功能缺陷集中在列表页与编辑页两处，登录与大屏本身工作正常，
明文口令属于安全弱点而非功能故障。

---

# 第二轮修复（数据正确性与安全）

## 4. 大屏出勤率口径不一致

顶部卡片用 `正常 / 应到`，趋势图用 `(正常+迟到+请假) / 应到`，同一天显示两个不同的数。
统一为 **出勤率 = 实到 / 应到，实到 = 正常 + 迟到**，由后端 `stats()` 计算 `today_rate`，
卡片与趋势图共用。无考勤记录的日期返回 `null` 画成断点；纵轴改为 0–100%，取消平滑。

## 5. 同一学生同一天可重复录入

数据库无约束，重复录入会让出勤率超过 100%。

- `schema.sql`：新增 `UNIQUE KEY uk_student_date (student_no, date)`（替代原 `idx_student_no`）；
  演示数据改为 `INSERT IGNORE`，重复导入不报错。
- 新增 / 编辑前先查重（编辑时排除自身），返回 409「该学生当天已有考勤记录」；
  并发下漏过预检查时，捕获 MySQL 1062 错误兜底。
- 已有数据库执行 `migrations/001_unique_student_date.sql` 补约束。

## 6. 新增 / 编辑接口没有服务端校验

原先只靠前端 `required`，绕过页面直接调接口可写入空学号、任意状态、非法日期；
出错时还会把数据库原始报错返回给页面。

- `AttendanceController.validate_record()`：学号必填且为 ≤20 位字母数字；姓名必填 ≤50 字；
  日期必须是真实存在的 `YYYY-MM-DD`（`2026-9-5` 规范化为 `2026-09-05`，`2026-02-30` 拒绝）；
  状态限定 正常/迟到/请假/旷课；时间 ≤20、备注 ≤200 字。多处错误一次全部列出，返回 400。
- 编辑不存在的记录返回 404。
- 异常只写日志，接口统一返回通用提示，不泄露数据库错误原文。
- 表单补充 `maxlength` / `pattern`，与后端规则一致。

## 7. 存储型 XSS

后台列表页与大屏异常名单把姓名、备注直接拼进 `innerHTML`。
在备注里存入 `<script>` 或 `<img onerror=...>`，任何打开页面的人都会执行。

- 两处均新增 `esc()`，对 `& < > " '` 转义后再拼接；记录 id 强制转为数字。

验证：在真实库里存入恶意载荷，旧版大屏执行了注入脚本（`window.__pwned = 1`），
修复后列表页与大屏均原样显示为文本、未执行。

---

# 第三轮：数据关联、安全加固与新功能

## 8. 考勤与学生名册关联（建议 4）

考勤表另存一份姓名、学号可以随便填，和名册没有关联：改了名册两边不一致，名册外的学号也会被计入统计。

- `attendance_record.student_no` 外键关联 `student.student_no`（`ON UPDATE CASCADE ON DELETE RESTRICT`）。
- 录入时从名册下拉选人，姓名由后端按学号从名册带出，不信任前端提交的姓名。
- 所有显示姓名的地方 `JOIN student`，名册改名后历史记录同步显示新名字。
- 新增"学生名册"页面：增删改学生；改学号自动同步考勤；有考勤记录的学生禁止删除。
- 旧库迁移：`migrations/002_link_student_roster.sql`（先把名册外学号补进名册，再加外键）。

## 9. 今日未登记学生不出现在任何统计里（建议 3）

`stats()` 以名册为准计算 `unregistered`；大屏新增"未登记"卡片，异常名单加入"未登记"类型，
环形图加入未登记扇区，保证 应到 = 正常 + 迟到 + 请假 + 旷课 + 未登记。

## 10. 调试模式对外开放（建议 6）

原 `run.py` 为 `debug=True` + `host='0.0.0.0'`，局域网内任何人可打开 Werkzeug 调试控制台执行任意代码。
改为默认 `127.0.0.1`、调试关闭，用 `HOST` / `FLASK_DEBUG` 环境变量开启；非本机地址强制关闭调试。

## 11. 重启后所有人掉线（建议 7）

`secret_key = os.urandom(24)` 每次启动都变。改为读 `SECRET_KEY` 环境变量，
没有则生成一次保存到 `instance/secret_key`（权限 600，已 gitignore）。
另外：session cookie 设置 `HttpOnly`、`SameSite=Lax`，有效期 8 小时；登录前清空旧 session 防会话固定。

## 12. 界面与体验（建议 8–12）

- 后台换用独立样式 `static/back/admin.css`，左侧加入真正的菜单（原 Simpla 模板那条深色栏只是背景图）；手机上菜单变为顶部横排、表格可左右滑动。
- 登录页改为 `<form>`，回车即可登录；原标题被模板样式隐藏，已修复。
- 大屏标题取名册里的班级名，7 张卡片配图标，状态用固定配色（原来"正常"是红色）；环形图中心改为与卡片同口径的出勤率。
- 异常名单固定高度可滚动，长备注自动换行，不再撑出屏幕。
- 列表页：日期范围 / 状态 / 关键字筛选 + 分页；关键字中的 `%` `_` 已转义，按普通字符匹配。
- 新增页日期默认今天，保存后保留日期、清空其他项，方便连续录入；`alert` 弹窗换成顶部提示条。
- 演示数据补满近 7 天，并留一名学生今天未登记，用来演示"未登记"统计。

## 13. 新功能（建议 13–15）

- **批量点名**：`/back/attendance/roll-call`，全班一页、默认正常、实时预览出勤率；
  用 `INSERT ... ON DUPLICATE KEY UPDATE` 在一个事务里保存，重复保存不会产生重复记录。
- **导出 Excel**：`/back/attendance/export`，沿用列表页的筛选条件，附"汇总"表；
  以 `=` 开头的单元格强制按文本写入，防止公式注入。
- **个人考勤统计**：`/back/student/<学号>?month=YYYY-MM`，各状态次数、个人出勤率与当月明细。

## 验证

- `smoke_test.py`：全部通过。
- 新增 `e2e_test.py`（真实 MariaDB + 运行中的服务）：36 项全部通过。
- 迁移脚本：在用最早版本 `schema.sql` 建的库（含一条名册外学号的考勤）上依次执行 001、002，成功，外键生效。
- 重启服务后旧 session cookie 仍有效；`HOST=0.0.0.0 FLASK_DEBUG=1` 启动时调试被自动关闭。
- 浏览器逐页点击（登录回车、筛选、导出、新增、重复提示、批量点名保存、名册、个人统计、大屏、手机宽度），无脚本错误。

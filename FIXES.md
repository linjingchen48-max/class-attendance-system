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

# 班级考勤管理系统

面向幼儿园 / 中小学班级考勤场景的管理工具：后台录入与管理考勤记录，前台以数据大屏展示出勤统计，替代纸质点名与人工汇总。

4 人小组课程项目，本人承担主要开发，覆盖数据库建模、后端接口到前端页面的完整链路。

## 技术栈

| 层 | 选型 |
| --- | --- |
| 后端 | Python 3.8+ · Flask · PyMySQL · openpyxl（导出 Excel） |
| 数据库 | MySQL 5.7+ / MariaDB 10.4+ |
| 前端 | Jinja2 模板 · 原生 JavaScript · ECharts |
| 口令 | Werkzeug PBKDF2 摘要 |

## 功能

**后台**（需登录）

- **考勤记录**：按日期范围、状态、姓名 / 学号筛选，分页浏览；筛选条件保存在地址栏，刷新不丢
- **批量点名**：选好日期，全班名单一次列出，默认"正常"，只需改少数异常的人，一键保存（已有记录会被覆盖，不会重复）
- **单条新增 / 编辑**：从学生名册里选人，日期默认今天
- **学生名册**：增删改学生；改学号时历史考勤自动跟着改，有考勤记录的学生不能删除
- **个人考勤统计**：按月查看某个学生的正常 / 迟到 / 请假 / 旷课次数、个人出勤率和明细
- **导出 Excel**：按当前筛选条件导出，附"汇总"工作表
- 支持正常 / 迟到 / 请假 / 旷课 4 种状态，可记录时间与备注

**前台数据大屏**

- 标题自动使用学生名册里的班级名
- 今日应到 / 实到 / 出勤率 / 迟到 / 请假 / 旷课 / **未登记** 7 项指标
- 今日考勤构成环形图、近 7 日出勤率折线（无记录的日子显示为断点）
- 今日异常名单（按 旷课 → 未登记 → 迟到 → 请假 排序）
- 每 30 秒自动刷新

**出勤率口径**（全站统一）：出勤率 = 实到 ÷ 应到，实到 = 正常 + 迟到，应到 = 学生名册人数。

**数据正确性与安全**

- 同一学生同一天只能有一条考勤（数据库唯一约束）；考勤学号必须在名册中（外键）
- 所有写接口都在服务端校验；出错只返回通用提示，详细错误写日志
- 页面显示用户输入前统一转义（防 XSS）；导出 Excel 时防公式注入
- 调试模式默认关闭、默认只监听本机；session 密钥固定保存，重启不掉线

## 项目结构

```
class-attendance-system/
├── app.py / run.py              # 应用工厂与启动入口（默认 127.0.0.1:5000）
├── routes/web.py                # 路由注册，共 24 条
├── controllers/
│   ├── HomeController.py        # 前台大屏与统计接口
│   ├── AdminController.py       # 登录 / 登出
│   ├── AttendanceController.py  # 考勤增删改查、筛选分页、批量点名、导出 Excel
│   └── StudentController.py     # 学生名册、个人考勤统计
├── models/
│   ├── database.py              # PyMySQL 连接与事务封装
│   ├── AttendanceModel.py       # 考勤记录与统计
│   ├── StudentModel.py          # 学生名册
│   └── TeacherModel.py          # 班主任账号与口令校验
├── templates/                   # 后台 7 页 + 前台大屏
├── static/                      # 样式与脚本（后台样式在 static/back/admin.css）
├── schema.sql                   # 建库建表与近 7 天演示数据（可重复导入）
├── migrations/                  # 旧数据库升级脚本
├── tools/set_password.py        # 重置账号口令
├── smoke_test.py                # 冒烟测试（不依赖真实数据库）
└── e2e_test.py                  # 端到端测试（真实数据库 + 运行中的服务）
```

数据表 3 张：`teacher`（班主任）、`student`（学生名册）、`attendance_record`（考勤记录，
"学号+日期"唯一，学号外键关联名册，另有日期 / 状态索引）。

## 本地运行

```bash
pip install -r requirements.txt

# ⚠️ 导入时必须指定 utf8mb4，否则中文会变成乱码
mysql --default-character-set=utf8mb4 -uroot -p < schema.sql

python run.py
```

打开 <http://127.0.0.1:5000/back/login>，演示账号 `admin` / `admin123`；
前台大屏在 <http://127.0.0.1:5000/front/>。

数据库连接通过环境变量覆盖，默认 `localhost:3306` / `root` / `root` / `dgcsxy`：

```bash
DB_HOST=127.0.0.1 DB_PORT=3306 DB_USER=root DB_PASSWORD=yourpass DB_NAME=dgcsxy python run.py
```

其他启动选项：

| 环境变量 | 作用 | 默认 |
| --- | --- | --- |
| `HOST` | 监听地址。上课演示要让同学用手机访问时设为 `0.0.0.0` | `127.0.0.1` |
| `PORT` | 端口 | `5000` |
| `FLASK_DEBUG` | 设为 `1` 开启调试（热重载 + 报错页）。只在本机生效，`HOST` 不是本机时自动关闭 | 关闭 |
| `SECRET_KEY` | session 签名密钥。不设置时自动生成并保存在 `instance/secret_key`（已忽略，不会提交） | 自动生成 |

### 关于字符集

`schema.sql` 里的演示数据含中文。若导入时未指定 `--default-character-set=utf8mb4`，
UTF-8 字节会被按 latin1 解释，库里存成乱码。表现是：大屏出勤率恒为 0、
异常名单把所有人都列出来 —— 因为程序用正确的 `'正常'` 去匹配，而库里存的是乱码。
遇到这种情况删库重新按上面的命令导入即可。

### 已有数据库升级

用旧版本 `schema.sql` 建的库，按顺序执行还没执行过的迁移（新导入的库不需要）：

```bash
mysql --default-character-set=utf8mb4 -uroot -p dgcsxy < migrations/001_unique_student_date.sql   # 学号+日期唯一
mysql --default-character-set=utf8mb4 -uroot -p dgcsxy < migrations/002_link_student_roster.sql   # 考勤关联名册
```

- 001 报 `Duplicate entry`：库里已有重复记录，按迁移文件里的查询找出后删掉多余的再执行。
- 002 会先把考勤里出现、名册里没有的学号自动补进名册（班级为空），再加外键。

## 修复记录

本项目在课程交付后做过三轮复盘：修复了出勤率口径、重复录入、缺少服务端校验、SQL 格式化缺陷、明文口令、存储型 XSS、调试模式外露等问题，并补充了学生名册、批量点名、筛选分页、导出 Excel、个人统计等功能，详见 [FIXES.md](FIXES.md)。

修复前后用同一套测试对照（真实 MySQL + PyMySQL）：原始代码 4 项失败，修复后全部通过。

## 测试

```bash
python smoke_test.py   # 不需要数据库
python e2e_test.py     # 需要先导入 schema.sql 并运行 python run.py
```

- `smoke_test.py`：以与 PyMySQL 相同的 `%` 格式化逻辑替换数据库层，覆盖登录、受保护路由、
  列表筛选分页、批量点名、导出 Excel（含防公式注入）、统计接口与未登录重定向。
- `e2e_test.py`：连真实数据库和运行中的服务，覆盖名册联动、重复录入、输入校验、批量点名、
  筛选分页、导出内容、个人统计、大屏未登记统计等 36 项。测试数据用 2020 年日期和 `E2E` 学号，结束自动清理。

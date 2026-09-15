# 班级考勤管理系统

面向幼儿园 / 中小学班级考勤场景的管理工具：后台录入与管理考勤记录，前台以数据大屏展示出勤统计，替代纸质点名与人工汇总。

4 人小组课程项目，本人承担主要开发，覆盖数据库建模、后端接口到前端页面的完整链路。

## 技术栈

| 层 | 选型 |
| --- | --- |
| 后端 | Python 3.8+ · Flask · PyMySQL |
| 数据库 | MySQL 5.7+ / MariaDB 10.4+ |
| 前端 | Jinja2 模板 · jQuery · ECharts |
| 口令 | Werkzeug PBKDF2 摘要 |

## 功能

**后台**（需登录）

- 基于 session 的登录鉴权，未登录访问受保护路由自动跳回登录页
- 考勤记录的新增、编辑、删除与列表查询
- 支持正常 / 迟到 / 请假 / 旷课 4 种状态，可记录时间与备注

**前台数据大屏**

- 在册学生人数
- 今日各状态人数分布
- 近 7 日出勤率折线
- 当日异常名单（按旷课 → 迟到 → 请假 排序）

## 项目结构

```
final_attendance_system/
├── app.py / run.py              # 应用工厂与启动入口（默认 5000 端口）
├── routes/web.py                # 路由注册，共 12 条
├── controllers/
│   ├── HomeController.py        # 前台大屏与统计接口
│   ├── AdminController.py       # 登录 / 登出
│   └── AttendanceController.py  # 考勤增删改查
├── models/
│   ├── database.py              # PyMySQL 连接与事务封装
│   ├── AttendanceModel.py       # 考勤记录与统计
│   └── TeacherModel.py          # 班主任账号与口令校验
├── templates/                   # 后台 4 页 + 前台大屏
├── static/                      # 样式与脚本
├── schema.sql                   # 建库建表与演示数据
├── tools/set_password.py        # 重置账号口令
└── smoke_test.py                # 冒烟测试（不依赖真实数据库）
```

数据表 3 张：`teacher`（班主任）、`student`（学生名册）、`attendance_record`（考勤记录，按日期 / 状态 / 学号建了 3 个索引）。

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

### 关于字符集

`schema.sql` 里的演示数据含中文。若导入时未指定 `--default-character-set=utf8mb4`，
UTF-8 字节会被按 latin1 解释，库里存成乱码。表现是：大屏出勤率恒为 0、
异常名单把所有人都列出来 —— 因为程序用正确的 `'正常'` 去匹配，而库里存的是乱码。
遇到这种情况删库重新按上面的命令导入即可。

## 修复记录

本项目在课程交付后做过一轮复盘，修复了 2 个功能缺陷和 1 个安全问题，详见 [FIXES.md](FIXES.md)。

修复前后用同一套测试对照（真实 MySQL + PyMySQL）：原始代码 4 项失败，修复后全部通过。

## 测试

```bash
python smoke_test.py
```

以与 PyMySQL 相同的 `%` 格式化逻辑替换数据库层，覆盖登录、受保护路由、
列表 / 编辑 / 统计接口与未登录重定向，无需连接真实数据库即可运行。

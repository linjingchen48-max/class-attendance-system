"""冒烟测试：用与 PyMySQL 同样的 % 格式化逻辑替换数据库层，验证修复后可正常运行。"""
import sys, types, pathlib
ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── 伪 pymysql，使 models.database 可导入
fake = types.ModuleType("pymysql"); fake.cursors = types.SimpleNamespace(DictCursor=object)
fake.connect = lambda **k: (_ for _ in ()).throw(RuntimeError("不应真正连库"))
sys.modules["pymysql"] = fake

from werkzeug.security import generate_password_hash
import models.database as db

EXECUTED = []
TEACHER = {"id": 1, "username": "admin", "name": "班主任",
           "password": generate_password_hash("admin123")}
RECORDS = [{"id": 1, "student_no": "20250001", "student_name": "李雷", "class_name": "一(1)班",
            "date": "2026-01-03", "status": "迟到", "time": "08:05", "remark": "=1+1"}]
STUDENTS = [{"id": 1, "student_no": "20250001", "student_name": "李雷", "class_name": "一(1)班",
             "record_count": 1}]

def _mogrify(sql, params):
    """完全复刻 PyMySQL.Cursor.mogrify：args is not None 时才做 % 格式化。"""
    if params is not None:
        sql = sql % tuple("'%s'" % p for p in params)
    return sql

def fetch_all(sql, params=None):
    q = _mogrify(sql, params); EXECUTED.append(q)
    # 按查询特征返回对应形状的行（模拟 DictCursor 每次返回新行）
    if "FROM teacher" in q:            return [dict(TEACHER)]
    if "COUNT(*) AS c" in q:           return [{"c": 5}]
    if "DISTINCT class_name" in q:     return [{"class_name": "一(1)班"}]
    if "AS recorded" in q:             return [{"present": 2, "late": 1, "leave": 1, "absent": 0, "recorded": 4}]
    if "GROUP BY `date`" in q:         return [{"d": "2026-01-03", "attended": 3}]
    if "record_count" in q:            return [dict(r) for r in STUDENTS]
    if "FROM student s" in q and "AS name" in q:
        return [{"student_no": "20250001", "name": "李雷", "type": "迟到", "time": "08:05", "remark": ""}]
    if "FROM student" in q:            return [dict(r) for r in STUDENTS]
    if "attendance_record" in q:       return [dict(r) for r in RECORDS]
    return []

def fetch_one(sql, params=None):
    rows = fetch_all(sql, params); return rows[0] if rows else None

def execute(sql, params=None):
    EXECUTED.append(_mogrify(sql, params)); return 1

def execute_many(sql, params_list):
    for p in params_list: EXECUTED.append(_mogrify(sql, p))

db.fetch_all, db.fetch_one, db.execute, db.execute_many = fetch_all, fetch_one, execute, execute_many
import models.AttendanceModel as AM, models.TeacherModel as TM, models.StudentModel as SM
AM.fetch_all, AM.fetch_one, AM.execute, AM.execute_many = fetch_all, fetch_one, execute, execute_many
SM.fetch_all, SM.fetch_one, SM.execute = fetch_all, fetch_one, execute
TM.fetch_one, TM.execute = fetch_one, execute

from app import create_app
app = create_app(); app.secret_key = "test"
c = app.test_client()
ok = lambda b: "✓" if b else "✗"
fails = 0

def check(label, cond, extra=""):
    global fails
    if not cond: fails += 1
    print(f"  {ok(cond)} {label}{(' — ' + extra) if extra else ''}")

print("── 登录流程")
r = c.get("/back/login");                                   check("登录页可访问", r.status_code == 200)
r = c.post("/back/login", data={"username":"admin","password":"admin123"})
check("正确口令登录", r.get_json().get("code") == 200, str(r.get_json()))
r2 = c.post("/back/login", data={"username":"admin","password":"wrong"})
# 注：桩忽略 SQL 的 WHERE 子句，原始代码靠 DB 过滤，因此本项只对修复后版本有意义
print(f"  · 错误口令 → code={r2.get_json().get('code')}（原版靠 DB 过滤，桩无法模拟，仅供参考）")

print("── 受保护路由（含修复的 DATE_FORMAT SQL）")
r = c.get("/back/attendance/list");      check("考勤列表页", r.status_code == 200, f"HTTP {r.status_code}")
r = c.get("/back/attendance/api/list")
j = r.get_json() or {}
check("列表 API（list_all）", r.status_code == 200 and j.get("code") == 200,
      f"HTTP {r.status_code} / body code={j.get('code')} {j.get('msg','')[:46]}")
r = c.get("/back/attendance/edit/1");    check("编辑页（get_by_id）", r.status_code == 200, f"HTTP {r.status_code}")

r = c.get("/back/attendance/api/list?start=2026-01-01&status=迟到&keyword=50%25_&page=1")
j = r.get_json() or {}
check("列表筛选 + 分页", j.get("code") == 200 and j.get("total") == 5, f"code={j.get('code')} total={j.get('total')}")
# 关键字 "50%_" 应变成 LIKE '%50\%\_%'：% 和 _ 按普通字符匹配
check("关键字里的 % _ 被转义", any(r"'%50\%\_%'" in q for q in EXECUTED[-3:]))

print("── 新功能页面")
for url, label in [("/back/attendance/roll-call", "批量点名页"), ("/back/student/list", "学生名册页"),
                   ("/back/student/20250001", "个人统计页"), ("/back/attendance/add", "新增页")]:
    r = c.get(url); check(label, r.status_code == 200, f"HTTP {r.status_code}")
r = c.get("/back/attendance/api/roll-call?date=2026-01-03")
check("点名表 API", (r.get_json() or {}).get("code") == 200)
r = c.post("/back/attendance/api/roll-call", json={"date": "2026-01-03", "items": [
    {"student_no": "20250001", "status": "正常", "time": "", "remark": ""}]})
check("批量保存", (r.get_json() or {}).get("code") == 200, (r.get_json() or {}).get("msg", ""))
r = c.post("/back/attendance/api/roll-call", json={"date": "2026-01-03", "items": [
    {"student_no": "99999999", "status": "正常"}]})
check("名册外学号被拒", (r.get_json() or {}).get("code") == 400)
r = c.get("/back/attendance/export")
ok_xlsx = r.status_code == 200 and r.data[:2] == b"PK"
check("导出 Excel", ok_xlsx, f"HTTP {r.status_code}")
if ok_xlsx:
    import io, openpyxl
    cell = openpyxl.load_workbook(io.BytesIO(r.data)).active["G2"]
    check("备注 =1+1 按文本导出（防公式注入）", cell.value == "=1+1" and cell.data_type == "s", f"type={cell.data_type}")

print("── 前台大屏")
r = c.get("/front/");                    check("大屏页", r.status_code == 200, f"HTTP {r.status_code}")
r = c.get("/front/api/stats")
j = r.get_json() or {}
check("统计 API（stats）", r.status_code == 200 and j.get("code", 200) == 200,
      f"HTTP {r.status_code} / body code={j.get('code')}")

print("── 未登录时应被挡回")
c2 = app.test_client()
r = c2.get("/back/attendance/list");     check("未登录重定向", r.status_code == 302, f"HTTP {r.status_code}")

print("── 明文口令是否泄漏到 SQL")
leaked = [q for q in EXECUTED if "admin123" in q]
check("SQL 中无明文口令", not leaked, f"{len(leaked)} 处" if leaked else "")

print(f"\n{'全部通过' if not fails else str(fails) + ' 项失败'}")
sys.exit(1 if fails else 0)

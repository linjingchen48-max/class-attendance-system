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
RECORDS = [{"id": 1, "student_no": "20250001", "student_name": "李雷",
            "date": "2026-01-03", "status": "迟到", "time": "08:05", "remark": "堵车"}]

def _mogrify(sql, params):
    """完全复刻 PyMySQL.Cursor.mogrify：args is not None 时才做 % 格式化。"""
    if params is not None:
        sql = sql % tuple("'%s'" % p for p in params)
    return sql

def fetch_all(sql, params=None):
    q = _mogrify(sql, params); EXECUTED.append(q)
    if "FROM teacher" in q:            return [dict(TEACHER)]   # 模拟 DictCursor 每次返回新行
    if "attendance_record" in q:       return [dict(r) for r in RECORDS]
    if "FROM student" in q:            return [{"c": 5}]
    return []

def fetch_one(sql, params=None):
    rows = fetch_all(sql, params); return rows[0] if rows else None

def execute(sql, params=None):
    EXECUTED.append(_mogrify(sql, params)); return 1

db.fetch_all, db.fetch_one, db.execute = fetch_all, fetch_one, execute
import models.AttendanceModel as AM, models.TeacherModel as TM
AM.fetch_all, AM.fetch_one, AM.execute = fetch_all, fetch_one, execute
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

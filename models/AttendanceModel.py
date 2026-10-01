from datetime import date, timedelta
from .database import fetch_all, fetch_one, execute, execute_many
from .StudentModel import StudentModel

STATUSES = ('正常', '迟到', '请假', '旷课')

# 姓名一律取名册里的（s.student_name），名册改名后历史记录跟着显示新名字；
# 极端情况下名册行缺失才退回记录里的快照。
_SELECT_RECORD = """SELECT a.id, a.student_no,
                           COALESCE(s.student_name, a.student_name) AS student_name,
                           COALESCE(s.class_name, '') AS class_name,
                           DATE_FORMAT(a.`date`, '%%Y-%%m-%%d') AS `date`,
                           a.status, COALESCE(a.time,'') AS time, COALESCE(a.remark,'') AS remark
                    FROM attendance_record a
                    LEFT JOIN student s ON s.student_no = a.student_no"""


def _build_filters(filters: dict):
    """把列表页的筛选条件拼成 WHERE 子句，全部走参数化，不拼接用户输入。"""
    where, params = [], []
    filters = filters or {}
    if filters.get("start"):
        where.append("a.`date` >= %s"); params.append(filters["start"])
    if filters.get("end"):
        where.append("a.`date` <= %s"); params.append(filters["end"])
    if filters.get("status") in STATUSES:
        where.append("a.status = %s"); params.append(filters["status"])
    if filters.get("keyword"):
        # 转义 LIKE 通配符，让用户输入的 % 和 _ 按普通字符匹配
        raw = filters["keyword"].replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        kw = "%" + raw + "%"
        where.append("(a.student_no LIKE %s OR COALESCE(s.student_name, a.student_name) LIKE %s)")
        params += [kw, kw]
    if filters.get("student_no"):
        where.append("a.student_no = %s"); params.append(filters["student_no"])
    return (" WHERE " + " AND ".join(where)) if where else "", params


class AttendanceModel:
    # ---------------- 列表 / 导出 ----------------
    @staticmethod
    def search(filters: dict = None, page: int = 1, page_size: int = 20):
        """按条件分页查询，返回 (当前页记录, 符合条件的总条数)。"""
        where_sql, params = _build_filters(filters)
        row = fetch_one(f"""SELECT COUNT(*) AS c FROM attendance_record a
                            LEFT JOIN student s ON s.student_no = a.student_no{where_sql}""",
                        tuple(params))
        total = int(row["c"]) if row else 0
        offset = (page - 1) * page_size
        rows = fetch_all(_SELECT_RECORD + where_sql +
                         " ORDER BY a.`date` DESC, a.student_no ASC LIMIT %s OFFSET %s",
                         tuple(params + [page_size, offset]))
        return rows, total

    @staticmethod
    def export_rows(filters: dict = None, limit: int = 50000):
        where_sql, params = _build_filters(filters)
        return fetch_all(_SELECT_RECORD + where_sql +
                         " ORDER BY a.`date` DESC, a.student_no ASC LIMIT %s",
                         tuple(params + [limit]))

    # 兼容旧调用：不带条件取最近 limit 条
    @staticmethod
    def list_all(limit: int = 500):
        rows, _ = AttendanceModel.search({}, 1, limit)
        return rows

    # ---------------- 单条增删改 ----------------
    @staticmethod
    def get_by_id(record_id: int):
        return fetch_one(_SELECT_RECORD + " WHERE a.id=%s LIMIT 1", (record_id,))

    @staticmethod
    def exists_on_date(student_no: str, date_str: str, exclude_id: int = None) -> bool:
        """该学生当天是否已有考勤记录（编辑时排除自身 exclude_id）。"""
        sql = "SELECT id FROM attendance_record WHERE student_no=%s AND `date`=%s"
        params = [student_no, date_str]
        if exclude_id is not None:
            sql += " AND id<>%s"
            params.append(exclude_id)
        return fetch_one(sql + " LIMIT 1", tuple(params)) is not None

    @staticmethod
    def add(student_no: str, student_name: str, date_str: str, status: str, time: str = "", remark: str = "") -> int:
        sql = """INSERT INTO attendance_record(student_no, student_name, `date`, status, time, remark)
                 VALUES(%s,%s,%s,%s,%s,%s)"""
        return execute(sql, (student_no, student_name, date_str, status, time, remark))

    @staticmethod
    def update(record_id: int, student_no: str, student_name: str, date_str: str, status: str, time: str = "", remark: str = "") -> int:
        sql = """UPDATE attendance_record
                 SET student_no=%s, student_name=%s, `date`=%s, status=%s, time=%s, remark=%s
                 WHERE id=%s"""
        execute(sql, (student_no, student_name, date_str, status, time, remark, record_id))
        return record_id

    @staticmethod
    def delete(record_id: int) -> int:
        execute("DELETE FROM attendance_record WHERE id=%s", (record_id,))
        return record_id

    # ---------------- 批量点名 ----------------
    @staticmethod
    def roll_call_sheet(date_str: str):
        """名册全员 + 当天已有的考勤（没有的为 None），用于批量点名页面。"""
        sql = """SELECT s.student_no, s.student_name, COALESCE(s.class_name,'') AS class_name,
                        a.id AS record_id, a.status, COALESCE(a.time,'') AS time,
                        COALESCE(a.remark,'') AS remark
                 FROM student s
                 LEFT JOIN attendance_record a ON a.student_no = s.student_no AND a.`date` = %s
                 ORDER BY s.student_no"""
        return fetch_all(sql, (date_str,))

    @staticmethod
    def save_roll_call(date_str: str, items):
        """一次保存全班当天考勤：没有记录的新增，已有的覆盖（依赖 学号+日期 唯一约束），在同一个事务里完成。"""
        sql = """INSERT INTO attendance_record(student_no, student_name, `date`, status, time, remark)
                 VALUES(%s,%s,%s,%s,%s,%s)
                 ON DUPLICATE KEY UPDATE student_name=VALUES(student_name), status=VALUES(status),
                                         time=VALUES(time), remark=VALUES(remark)"""
        execute_many(sql, [(it["student_no"], it["student_name"], date_str,
                            it["status"], it["time"], it["remark"]) for it in items])

    # ---------------- 个人统计 ----------------
    @staticmethod
    def student_month(student_no: str, month_start: date):
        """某学生某个月的考勤明细与各状态次数。"""
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        rows = fetch_all(_SELECT_RECORD + """ WHERE a.student_no=%s AND a.`date` >= %s AND a.`date` < %s
                                             ORDER BY a.`date` DESC""",
                         (student_no, month_start.isoformat(), next_month.isoformat()))
        counts = {s: 0 for s in STATUSES}
        for r in rows:
            if r["status"] in counts:
                counts[r["status"]] += 1
        recorded = len(rows)
        attended = counts["正常"] + counts["迟到"]
        return {
            "records": rows,
            "counts": counts,
            "recorded_days": recorded,
            "rate": round(attended / recorded * 100, 1) if recorded else None,
        }

    # ---------------- 大屏统计 ----------------
    @staticmethod
    def stats():
        today = date.today()
        total = StudentModel.count()

        # 出勤率口径（全站统一）：实到 / 应到
        #   实到 = 正常 + 迟到（人到了课堂，迟到也算到）
        #   应到 = 学生名册总人数
        # 请假、旷课、今天还没登记的都不计入实到。
        def attendance_rate(attended: int) -> float:
            return round((attended / total) * 100, 1) if total else 0.0

        sql_today = """SELECT
            SUM(CASE WHEN a.status='正常' THEN 1 ELSE 0 END) AS present,
            SUM(CASE WHEN a.status='迟到' THEN 1 ELSE 0 END) AS late,
            SUM(CASE WHEN a.status='请假' THEN 1 ELSE 0 END) AS `leave`,
            SUM(CASE WHEN a.status='旷课' THEN 1 ELSE 0 END) AS absent,
            COUNT(*) AS recorded
          FROM attendance_record a
          JOIN student s ON s.student_no = a.student_no
          WHERE a.`date`=%s"""
        row = fetch_one(sql_today, (today.isoformat(),)) or {}
        today_attendance = {k: int(row.get(k) or 0) for k in ("present", "late", "leave", "absent")}
        today_attendance["attended"] = today_attendance["present"] + today_attendance["late"]
        today_attendance["unregistered"] = max(total - int(row.get("recorded") or 0), 0)
        today_rate = attendance_rate(today_attendance["attended"])

        # 近 7 天：当天没有任何考勤记录时返回 None（前端画成断点），
        # 避免把"没录数据"误显示成"全班缺勤"。
        start = today - timedelta(days=6)
        sql_week = """SELECT DATE_FORMAT(`date`, '%%Y-%%m-%%d') AS d,
                             SUM(CASE WHEN status IN ('正常','迟到') THEN 1 ELSE 0 END) AS attended
                      FROM attendance_record
                      WHERE `date` BETWEEN %s AND %s
                      GROUP BY `date`"""
        by_day = {r["d"]: int(r["attended"] or 0)
                  for r in fetch_all(sql_week, (start.isoformat(), today.isoformat()))}
        weekly, weekly_labels = [], []
        for i in range(7):
            d = (start + timedelta(days=i)).isoformat()
            weekly_labels.append(d[5:].replace("-", "/"))
            weekly.append(attendance_rate(by_day[d]) if d in by_day else None)

        # 异常名单：今天 旷课 / 未登记 / 迟到 / 请假 的学生，按严重程度排序
        sql_abn = """SELECT s.student_no, s.student_name AS name,
                            COALESCE(a.status, '未登记') AS type,
                            COALESCE(NULLIF(a.time,''), '--') AS time,
                            COALESCE(a.remark, '') AS remark
                     FROM student s
                     LEFT JOIN attendance_record a ON a.student_no = s.student_no AND a.`date` = %s
                     WHERE a.id IS NULL OR a.status <> '正常'
                     ORDER BY FIELD(COALESCE(a.status,'未登记'), '旷课','未登记','迟到','请假'), s.student_no"""
        abnormal_list = fetch_all(sql_abn, (today.isoformat(),)) or []

        return {
            "class_name": StudentModel.class_label(),
            "total_students": total,
            "today_attendance": today_attendance,
            "today_rate": today_rate,
            "weekly_rate": weekly,
            "weekly_labels": weekly_labels,
            "abnormal_list": abnormal_list,
        }

from datetime import date, timedelta
from .database import fetch_all, fetch_one, execute


class AttendanceModel:
    @staticmethod
    def list_all(limit: int = 500):
        sql = """SELECT id, student_no, student_name, DATE_FORMAT(`date`, '%%Y-%%m-%%d') AS `date`,
                        status, time, remark
                 FROM attendance_record
                 ORDER BY `date` DESC, id DESC
                 LIMIT %s"""
        return fetch_all(sql, (limit,))

    @staticmethod
    def get_by_id(record_id: int):
        sql = """SELECT id, student_no, student_name, DATE_FORMAT(`date`, '%%Y-%%m-%%d') AS `date`,
                        status, time, remark
                 FROM attendance_record
                 WHERE id=%s LIMIT 1"""
        return fetch_one(sql, (record_id,))

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
        sql = "DELETE FROM attendance_record WHERE id=%s"
        execute(sql, (record_id,))
        return record_id

    @staticmethod
    def _total_students_fallback() -> int:
        # Prefer student table if exists; else count distinct student_no from records
        try:
            row = fetch_one("SELECT COUNT(*) AS c FROM student", ())
            return int(row["c"]) if row and row.get("c") is not None else 0
        except Exception:
            row = fetch_one("SELECT COUNT(DISTINCT student_no) AS c FROM attendance_record", ())
            return int(row["c"]) if row and row.get("c") is not None else 0

    @staticmethod
    def stats():
        today = date.today()
        total = AttendanceModel._total_students_fallback()

        # Today's counts by status
        sql_today = """SELECT
            SUM(CASE WHEN status='正常' THEN 1 ELSE 0 END) AS present,
            SUM(CASE WHEN status='迟到' THEN 1 ELSE 0 END) AS late,
            SUM(CASE WHEN status='请假' THEN 1 ELSE 0 END) AS `leave`,
            SUM(CASE WHEN status='旷课' THEN 1 ELSE 0 END) AS absent
          FROM attendance_record
          WHERE `date`=%s"""
        row = fetch_one(sql_today, (today.isoformat(),)) or {}
        today_attendance = {
            "present": int(row.get("present") or 0),
            "late": int(row.get("late") or 0),
            "leave": int(row.get("leave") or 0),
            "absent": int(row.get("absent") or 0),
        }

        # 出勤率口径（全站统一）：实到 / 应到
        #   实到 = 正常 + 迟到（人到了课堂，迟到也算到）
        #   应到 = 在册学生总数
        # 请假、旷课都不计入实到。
        def attendance_rate(attended: int) -> float:
            return round((attended / total) * 100, 1) if total else 0.0

        today_attendance["attended"] = today_attendance["present"] + today_attendance["late"]
        today_rate = attendance_rate(today_attendance["attended"])

        # Weekly rate (last 7 days, including today)
        # 当天没有任何考勤记录时返回 None（前端画成断点），而不是 0%，
        # 避免把"没录数据"误显示成"全班缺勤"。
        weekly = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            sql_day = """SELECT
                COUNT(*) AS recorded,
                SUM(CASE WHEN status IN ('正常','迟到') THEN 1 ELSE 0 END) AS attended
              FROM attendance_record
              WHERE `date`=%s"""
            r = fetch_one(sql_day, (d.isoformat(),)) or {}
            if not int(r.get("recorded") or 0):
                weekly.append(None)
                continue
            weekly.append(attendance_rate(int(r.get("attended") or 0)))

        # Abnormal list: today's records not normal
        sql_abn = """SELECT student_name AS name, status AS type,
                        COALESCE(NULLIF(time,''),'--') AS time,
                        COALESCE(remark,'') AS remark
                   FROM attendance_record
                   WHERE `date`=%s AND status <> '正常'
                   ORDER BY FIELD(status,'旷课','迟到','请假'), id DESC
                   LIMIT 8"""
        abnormal_list = fetch_all(sql_abn, (today.isoformat(),)) or []

        return {
            "total_students": total,
            "today_attendance": today_attendance,
            "today_rate": today_rate,
            "weekly_rate": weekly,
            "abnormal_list": abnormal_list
        }

from .database import fetch_all, fetch_one, execute


class StudentModel:
    """学生名册。应到人数、考勤录入选人、姓名显示都以这张表为准。"""

    @staticmethod
    def list_all():
        sql = """SELECT s.id, s.student_no, s.student_name, COALESCE(s.class_name,'') AS class_name,
                        COUNT(a.id) AS record_count
                 FROM student s
                 LEFT JOIN attendance_record a ON a.student_no = s.student_no
                 GROUP BY s.id, s.student_no, s.student_name, s.class_name
                 ORDER BY s.student_no"""
        return fetch_all(sql)

    @staticmethod
    def get_by_no(student_no: str):
        sql = """SELECT id, student_no, student_name, COALESCE(class_name,'') AS class_name
                 FROM student WHERE student_no=%s LIMIT 1"""
        return fetch_one(sql, (student_no,))

    @staticmethod
    def get_by_id(student_id: int):
        sql = """SELECT id, student_no, student_name, COALESCE(class_name,'') AS class_name
                 FROM student WHERE id=%s LIMIT 1"""
        return fetch_one(sql, (student_id,))

    @staticmethod
    def no_taken(student_no: str, exclude_id: int = None) -> bool:
        sql = "SELECT id FROM student WHERE student_no=%s"
        params = [student_no]
        if exclude_id is not None:
            sql += " AND id<>%s"
            params.append(exclude_id)
        return fetch_one(sql + " LIMIT 1", tuple(params)) is not None

    @staticmethod
    def add(student_no: str, student_name: str, class_name: str = "") -> int:
        sql = "INSERT INTO student(student_no, student_name, class_name) VALUES(%s,%s,%s)"
        return execute(sql, (student_no, student_name, class_name or None))

    @staticmethod
    def update(student_id: int, student_no: str, student_name: str, class_name: str = "") -> int:
        # 学号变更由外键 ON UPDATE CASCADE 同步到考勤记录
        sql = "UPDATE student SET student_no=%s, student_name=%s, class_name=%s WHERE id=%s"
        execute(sql, (student_no, student_name, class_name or None, student_id))
        return student_id

    @staticmethod
    def delete(student_id: int) -> int:
        execute("DELETE FROM student WHERE id=%s", (student_id,))
        return student_id

    @staticmethod
    def record_count(student_no: str) -> int:
        row = fetch_one("SELECT COUNT(*) AS c FROM attendance_record WHERE student_no=%s", (student_no,))
        return int(row["c"]) if row else 0

    @staticmethod
    def count() -> int:
        row = fetch_one("SELECT COUNT(*) AS c FROM student")
        return int(row["c"]) if row and row.get("c") is not None else 0

    @staticmethod
    def class_label() -> str:
        """大屏标题用的班级名：名册里只有一个班就用它，多个班用"、"连接，没有则为空。"""
        rows = fetch_all("""SELECT DISTINCT class_name FROM student
                            WHERE class_name IS NOT NULL AND class_name<>''
                            ORDER BY class_name""")
        return "、".join(r["class_name"] for r in rows)

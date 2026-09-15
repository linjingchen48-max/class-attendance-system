from werkzeug.security import generate_password_hash, check_password_hash

from .database import fetch_one, execute


class TeacherModel:
    @staticmethod
    def get_by_login(username: str, password: str):
        """按用户名取出记录后校验口令摘要。

        不再用 WHERE password=%s 直接比对明文：数据库只存 PBKDF2 摘要，
        校验交给 check_password_hash（内部为定时安全比较）。
        """
        sql = "SELECT id, username, name, password FROM teacher WHERE username=%s LIMIT 1"
        row = fetch_one(sql, (username,))
        if not row:
            return None
        if not check_password_hash(row["password"], password):
            return None
        # 构造新字典返回，不原地修改数据层给出的行（避免副作用）
        return {"id": row["id"], "username": row["username"], "name": row.get("name")}

    @staticmethod
    def create(username: str, password: str, name: str = "") -> int:
        sql = "INSERT INTO teacher(username, password, name) VALUES(%s,%s,%s)"
        return execute(sql, (username, generate_password_hash(password), name))

    @staticmethod
    def set_password(username: str, password: str) -> int:
        sql = "UPDATE teacher SET password=%s WHERE username=%s"
        return execute(sql, (generate_password_hash(password), username))

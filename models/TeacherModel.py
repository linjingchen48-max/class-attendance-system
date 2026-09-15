from .database import fetch_one, execute


class TeacherModel:
    @staticmethod
    def get_by_login(username: str, password: str):
        sql = "SELECT id, username, name FROM teacher WHERE username=%s AND password=%s LIMIT 1"
        return fetch_one(sql, (username, password))

    @staticmethod
    def create(username: str, password: str, name: str = "") -> int:
        sql = "INSERT INTO teacher(username, password, name) VALUES(%s,%s,%s)"
        return execute(sql, (username, password, name))

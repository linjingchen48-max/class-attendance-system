"""重置某个班主任账号的口令（写入 PBKDF2 摘要）。

用法：
    python tools/set_password.py admin 新口令
在项目根目录执行；数据库连接沿用 models/database.py 的环境变量配置。
"""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.TeacherModel import TeacherModel


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 1
    username, password = sys.argv[1], sys.argv[2]
    TeacherModel.set_password(username, password)
    print(f"已更新 {username} 的口令")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

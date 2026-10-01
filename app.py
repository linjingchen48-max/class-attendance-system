import logging
import os
import secrets
from datetime import timedelta

from flask import Flask

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_FILE = os.path.join(BASE_DIR, 'instance', 'secret_key')


def _load_secret_key() -> str:
    """session 签名密钥。

    优先读环境变量 SECRET_KEY；没有就在 instance/secret_key 里生成一次并保存，
    之后每次启动都复用它。以前每次启动都 os.urandom，重启后所有人都被踢下线。
    instance/ 已加入 .gitignore，密钥不会被提交到仓库。
    """
    key = os.getenv('SECRET_KEY')
    if key:
        return key
    try:
        with open(SECRET_FILE, encoding='utf-8') as f:
            key = f.read().strip()
        if key:
            return key
    except FileNotFoundError:
        pass
    os.makedirs(os.path.dirname(SECRET_FILE), exist_ok=True)
    key = secrets.token_hex(32)
    # 仅当前用户可读写
    fd = os.open(SECRET_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as f:
        f.write(key)
    return key


def create_app():
    app = Flask(__name__,
                template_folder='templates',  # 模板目录
                static_folder='static')       # 全局静态资源目录

    app.secret_key = _load_secret_key()
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,          # 前端脚本读不到 session cookie
        SESSION_COOKIE_SAMESITE='Lax',         # 降低跨站请求伪造风险
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    )
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

    # register routes
    with app.app_context():
        from routes.web import register_routes
        register_routes(app)

    return app

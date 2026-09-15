from flask import Flask
import os

def create_app():
    app = Flask(__name__,
                template_folder='templates',  # 模板目录
                static_folder='static')       # 全局静态资源目录

    # secret key for session
    app.secret_key = os.urandom(24)

    # register routes
    with app.app_context():
        from routes.web import register_routes
        register_routes(app)

    return app

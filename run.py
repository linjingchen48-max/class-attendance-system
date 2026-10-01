import os

from app import create_app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 默认只监听本机、关闭调试模式。
    # 调试模式自带的网页控制台可以执行任意 Python 代码，绝不能和 0.0.0.0 一起对外开放。
    #
    #   本机开发（热重载 + 报错页面）：FLASK_DEBUG=1 python run.py
    #   让同一局域网的人访问（如上课演示）：HOST=0.0.0.0 python run.py
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', '0') == '1'

    if debug and host not in ('127.0.0.1', 'localhost'):
        print('⚠️  调试模式只允许在本机使用，已自动关闭调试模式。')
        debug = False

    app.run(host=host, port=port, debug=debug)

from app import create_app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 开发环境配置：允许外部访问、热重载、端口5000
    app.run(host='0.0.0.0', port=5000, debug=True)
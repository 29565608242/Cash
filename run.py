import os
os.environ['FLASK_ENV'] = 'development'

from app import app

if __name__ == '__main__':
    # 使用8080端口启动服务，避免与其他应用冲突
    PORT = 8080
    try:
        app.run(
            host='0.0.0.0',
            port=PORT,
            debug=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n[结束] 服务已停止")
    except Exception as e:
        print("\n[错误] 启动失败: %s" % e)

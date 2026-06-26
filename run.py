import os

os.environ.setdefault('FLASK_ENV', 'development')

import cash_app.bootstrap  # noqa: F401
from cash_app.app_state import app, config

if __name__ == '__main__':
    port = int(os.getenv('PORT', config.PORT))
    app.logger.info('=' * 50)
    app.logger.info(f'启动 {config.APP_NAME}')
    app.logger.info(f"环境: {os.getenv('FLASK_ENV', 'development')}")
    app.logger.info(f'主机: {config.HOST}:{port}')
    app.logger.info('=' * 50)
    try:
        app.run(
            host=config.HOST,
            port=port,
            debug=app.config.get('DEBUG', False),
            use_reloader=True,
        )
    except KeyboardInterrupt:
        print("\n[结束] 服务已停止")
    except Exception as e:
        print("\n[错误] 启动失败: %s" % e)

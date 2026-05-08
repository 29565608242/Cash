from cash_app import *  # noqa: F401,F403
from cash_app.app_state import app, config

if __name__ == '__main__':
    import os

    port = int(os.getenv('PORT', config.PORT))
    app.logger.info('=' * 50)
    app.logger.info(f'启动 {config.APP_NAME}')
    app.logger.info(f"环境: {os.getenv('FLASK_ENV', 'development')}")
    app.logger.info(f'主机: {config.HOST}:{port}')
    app.logger.info('=' * 50)
    app.run(
        host=config.HOST,
        port=port,
        debug=app.config.get('DEBUG', False)
    )


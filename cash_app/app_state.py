import os
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from config import get_config

if __name__ == '__main__':
    sys.modules['app'] = sys.modules['__main__']

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(
    __name__.split('.')[0],
    static_folder=os.path.join(BASE_DIR, 'static'),
    template_folder=os.path.join(BASE_DIR, 'templates')
)
config = get_config()
config.init_app()

app.config.from_object(config)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.jinja_env.auto_reload = True
app.secret_key = config.SECRET_KEY
DATA_FILE = config.DATA_FILE_PATH

db = SQLAlchemy(app)


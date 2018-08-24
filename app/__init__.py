from flask import Flask
from config import Config
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from flask_mail import Mail
import flask_profiler

import logging
from logging.handlers import RotatingFileHandler
import os

app = Flask(__name__)
app.config.from_object(Config)
bootstrap = Bootstrap(app)
login = LoginManager(app)
login.login_view = 'login'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
app.jinja_env.trim_blocks=True
app.jinja_env.lstrip_blocks=True
cache = Cache(app, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache'})
mail = Mail(app)
app.config['flask_profiler'] = {
    'enabled': True,
    'storage': {
        'engine': 'sqlite'
    },
    'basicAuth': {
        'enabled': True,
        'username': 'randall',
        'password': 'secret'
    },
    'ignore': [
        '^/static/.*'
    ]
}

if not os.path.exists('logs'):
    os.mkdir('logs')
file_handler = RotatingFileHandler('logs/ftt.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('FencingTournamentTool startup')

from app import routes, models

from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import RotatingFileHandler
from celery import Celery


# app
app = Flask(__name__) 
app.config.from_object(Config)

# database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# login 
login = LoginManager(app)
login.login_view = 'login' # to protect user from unauthorized pages

# logging system
if not app.debug:

    # the roating file handler limits the number of logs we see
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=30)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application')


# asynchronous jobs through celerey
app.config['CELERY_BROKER_URL'] = 'redis://127.0.0.1:6379/0' # if we want a broker on a different machine
app.config['CELERY_RESULT_BACKEND'] = 'redis://127.0.0.1:6379/0'

celery_handler = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], backend=app.config['CELERY_RESULT_BACKEND'])
celery_handler.conf.update(app.config)


from app import routes, models, errors
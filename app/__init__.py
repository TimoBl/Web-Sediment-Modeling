from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import RotatingFileHandler
from redis import Redis
import rq
from flask_moment import Moment


# app
app = Flask(__name__,
            static_folder='assets', # for our static assets
            template_folder='templates') # for our html templates
app.config.from_object(Config)

# database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# login 
login = LoginManager(app)
login.login_view = 'login' # to protect user from unauthorized pages

# redis
app.redis = Redis.from_url(app.config['REDIS_URL'])
app.task_queue = rq.Queue('submission-tasks', connection=app.redis) # queue for submitting tasks
# kill : sudo service redis-server stop // killall redis-server

# time keeping
moment = Moment(app)

# logging system
if not app.debug:

    # the roating file handler limits the number of logs we see
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=30)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    
    # logging system
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application')

# sudo service redis-server stop 
from app import models, errors, routes
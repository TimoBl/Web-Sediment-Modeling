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
import os
from app.tasks import preprocess_data


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
app.redis = Redis(host='redis', port=6379)  #app.redis = Redis.from_url(app.config['REDIS_URL']) # kill : sudo service redis-server stop || killall redis-server
app.task_queue = rq.Queue('submission-tasks', connection=app.redis) # queue for submitting tasks
# sudo service redis-server stop 

# time keeping
moment = Moment(app)

# logging system
if not app.debug:

    # the roating file handler limits the number of logs we see
    file_handler = RotatingFileHandler('app/logs/app.log', maxBytes=10240, backupCount=30)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    
    # logging system
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Application')

# prepares the data for computation -> takes about 5 minutes to start the server
# preprocess_data()

from app import models, errors, routes

# run app
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
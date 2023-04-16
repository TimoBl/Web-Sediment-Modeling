from flask import Flask
from app.config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# app
app = Flask(__name__) 
app.config.from_object(Config)

# database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# login 
login = LoginManager(app)
login.login_view = 'login' # to protect user from unauthorized pages

from app import routes, models
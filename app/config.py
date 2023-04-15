import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
	# used for authentification
	SECRET_KEY = os.environ.get("SECRET_KEY") or "K:},y]yogU4j}ep40+yK" # hard coded secret key

	# used for databases
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db') # by default we use a database called app.db
	SQLALCHEMY_TRACK_MODIFICATIONS = False # don't to need to send a signal each time a database is changed


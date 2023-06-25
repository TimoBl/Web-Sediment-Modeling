import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	# used for authentification
	SECRET_KEY = os.environ.get("SECRET_KEY") or "K:},y]yogU4j}ep40+yK" # hard coded secret key

	# used to storage
	OUTPUT_DIR = "simulations" # where our simulation are stored

	# used for databases
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(os.path.abspath(os.getcwd()), OUTPUT_DIR, 'app.db') # by default we use a databse
	SQLALCHEMY_TRACK_MODIFICATIONS = False # don't to need to send a signal each time a database is changed

	# settings
	JOB_TIMEOUT = 10*60 # maximum of 10 minutes for job to complete

	# used for redis queue
	#REDIS_URL = os.environ.get('REDIS_URL') or "redis://redis:6379" #'redis://'
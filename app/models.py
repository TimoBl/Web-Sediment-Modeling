# here we define the schema of the database
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import redis
import rq
from app import app, db, login, moment


# User class
class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))

	def set_password(self, password):
		# for added security we hash our password
		self.password_hash = generate_password_hash(password)
		db.session.commit()

	def check_password(self, password):
		# here we compare the password to the hash
		return check_password_hash(self.password_hash, password)

	def get_submissions(self):
		# returns user's submissions
		own = Submission.query.filter_by(user_id=self.id) # we search for submissions with our id
		return own.order_by(Submission.timestamp.desc()) # and return the newest first

	def __repr__(self):
		return '<User {}>'.format(self.username)


@login.user_loader
def load_user(id):
	# loads a user given the id
	return User.query.get(int(id))


# Job Submission for calculations
class Submission(db.Model):
	id = db.Column(db.String(36), primary_key=True)
	name = db.Column(db.String(20)) # same as project name 
	timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow) # time of submission
	user_id = db.Column(db.Integer, db.ForeignKey('user.id')) # id of user who submitted the job
	status = db.Column(db.String(20), default="submitted") # status of the job 
	complete = db.Column(db.Boolean, default=False) # if job is successfully finished 

	def get_rq_job(self):
		try:
			rq_job = rq.job.Job.fetch(self.id, connection=app.redis)
		except (redis.exceptions.RedisError, rq.exceptions.NoSuchJobError):
			return None
		return rq_job

	def get_progress(self):

		# the job is still in progress
		if not self.complete:
			
			# so we want to get an update
			job = self.get_rq_job()
			self.status = job.meta.get('status', "submitted") if job is not None else "submitted"
			self.complete = bool(job.meta.get('complete', False) if job is not None else False)

			# check if job was completed
			if self.complete:
				# we could notify the user
				pass

			# update session
			db.session.commit()
		
		#job = self.get_rq_job()
		#return job.meta.get('status', 0) if job is not None else 100
		return self.status, self.complete


	def __repr__(self):
		self.get_progress()
		#return self
		return self
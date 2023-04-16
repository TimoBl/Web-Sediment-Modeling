from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


# here we define the schema of the database
class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))

	def set_password(self, password):
		# for added security we hash our password
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		# here we compare the password to the hash
		return check_password_hash(self.password_hash, password)

	def __repr__(self):
		return '<User {}>'.format(self.username)



@login.user_loader
def load_user(id):
	# loads a user given the id
	return User.query.get(int(id))
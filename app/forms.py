from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, DecimalField, FloatField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from app.models import User


# for user login
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


# for user registration
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')]) # used as second validation
    submit = SubmitField('Register')

    def validate_username(self, username):
        # check if username has already been registered
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username')


    def validate_email(self, email):
        # check if email has already been registered
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address')


# for simulation submission 
class JobSubmissionForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()], default="Demo")

    width =  IntegerField("Width", validators=[DataRequired()], default=50)
    height =  IntegerField("Height", validators=[DataRequired()], default=50)
    depth =  IntegerField("Depth", validators=[DataRequired()], default=50)

    sw =  FloatField("Spacing x", validators=[DataRequired()], default=1)
    sh =  FloatField("Spacing y", validators=[DataRequired()], default=1)
    sd =  FloatField("Spacing z", validators=[DataRequired()], default=0.1)

    submit = SubmitField('run')
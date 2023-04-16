from flask import render_template, flash, redirect, url_for
from app import app, db
from app.model import GeoModel
from app.models import User
from app.forms import LoginForm, RegistrationForm, JobSubmissionForm
from flask import request
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required


@app.route('/')
@app.route('/index')
def index():
    #user = {'username': 'Timo'}

    return render_template('index.html', title='Home')#, user=user)


@app.route('/login', methods=['GET', 'POST']) 
def login():

    # check if user is already authentificated
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # otherwise we submit a login form
    form = LoginForm()

    # checks if all the submission is valid
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first() # find user

        # check if username and password is correct
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        # we can log the user in
        login_user(user, remember=form.remember_me.data)

        # check if we need to redirect the user to a defined page
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index') # default

        return redirect(next_page)

    return render_template('login.html', title='Sign in', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():

    # check if user is already authenticated
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # submit registration form 
    form = RegistrationForm()

    # check if all the submission is valid
    if form.validate_on_submit():

        # add user to database
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        # we can log the user in
        login_user(user, remember=False)
        return redirect(url_for('index')) # we should log him 

    # otherwise send registration form
    return render_template('register.html', title='Register', form=form)


# run our computational model
@app.route('/model', methods=['GET', 'POST'])
@login_required # user needs to be logged in
def model():

    # get form
    form = JobSubmissionForm()

    # check if submission is valid
    if form.validate_on_submit():
        
        # get model
        dim = (form.width.data, form.height.data, form.depth.data)
        spacing = (form.sw.data, form.sh.data, form.sd.data)
        m = GeoModel(form.name.data, dim, spacing)
        
        # with three levels of simulation
        m.compute_surf(2)
        m.compute_facies(2)
        m.compute_prop(1)

        return str(m.get_units_domains_realizations())


    # otherwise send model form
    return render_template('model.html', title='Model', form=form)#, user=user)
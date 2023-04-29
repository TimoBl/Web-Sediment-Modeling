from flask import render_template, flash, redirect, url_for
from app import app, db
from app.models import User, Submission
from app.forms import LoginForm, RegistrationForm, JobSubmissionForm
from flask import request
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
import os
from rq.job import Job
#from rq import Callback

# for developpemnt only
import numpy as np
import shutil


@app.route('/')
@app.route('/index')
def index():
    # check if user is authenticated
    if current_user.is_authenticated:

        # if yes can show submissons
        submissions = current_user.get_submissions().all()
        return render_template('index.html', title='Home', submissions=submissions)
    
    return render_template('index.html', title='Home')


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


# logs the user our
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# registers a user
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

        # create output directory for user (this)
        try:
            os.mkdir(os.path.join("output", str(user.id))) 
        except Exception as e:
            print("Could not create directory for user {}!".format(d))
            print(e)

        # we can log the user in
        login_user(user, remember=False)
        return redirect(url_for('index')) # we should log him 

    # otherwise send registration form
    return render_template('register.html', title='Register', form=form)


# submit job
@app.route('/model', methods=['GET', 'POST'])
@login_required # user needs to be logged in
def model():

    # get form
    form = JobSubmissionForm()

    # check if submission is valid
    if form.validate_on_submit():

        # get variables
        name = form.name.data
        dim = (form.width.data, form.height.data, form.depth.data)
        spacing = (form.sw.data, form.sh.data, form.sd.data)
                           
        # get the job into queue
        job = Job.create('tasks.run_geo_model', args=(current_user.id, name, dim, spacing), connection=app.redis)
        rq_job = app.task_queue.enqueue_job(job)

        # show job submission
        submission = Submission(id=rq_job.get_id(), name=form.name.data, user_id=current_user.id)
        db.session.add(submission)
        db.session.commit()
        
        return redirect(url_for('index'))

    return render_template('model.html', title='Model', form=form)#, user=user) #str(m.get_units_domains_realizations())


# views the result of a job
@app.route('/view', methods=['GET', 'POST'])
@login_required # user needs to be logged in
def view():

    # get the submission id
    submission_id = request.args.get('id', None)

    # find submission
    submission = Submission.query.filter_by(id=submission_id).first()

    # check if submission is valid and from the same user
    if submission is not None and submission.user_id==current_user.id and submission.complete:

        # we can view the results
        out_dir = os.path.join("output", str(current_user.id), str(submission.id), "realizations.npy") 
        realizations = np.load(out_dir)

        return str(realizations)

    else:
        # we could add an error for each error type
        flash('Submission {} cannot be viewed'.format(submission_id))


    return redirect(url_for('index'))


# deletes a submission
@app.route('/delete', methods=['GET', 'POST'])
@login_required # user needs to be logged in
def delete():

    # get the submission id
    submission_id = request.args.get('id', None)

    # find submission
    submission = Submission.query.filter_by(id=submission_id).first()

    # check if submission is valid and from the same user
    if submission is not None and submission.user_id==current_user.id:

        # delete from databse
        db.session.delete(submission)
        db.session.commit()

        # delete output directory
        out_dir = os.path.join("output", str(current_user.id), str(submission.id))
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)

        flash('Submission {} was deleted'.format(submission_id))
    else:
        flash('Submission {} could not be deleted'.format(submission_id))

    return redirect(url_for('index'))
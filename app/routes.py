from flask import render_template, flash, redirect, url_for, send_file, jsonify
from app import app, db
from app.models import User, Submission
from app.forms import LoginForm, RegistrationForm #, JobSubmissionForm
from flask import request
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
import os
from rq.job import Job
from flask_bootstrap import Bootstrap
import numpy as np
import shutil
import json
import pandas as pd
import app.tasks as tasks
from app.tasks import run_model, generate_visualization
import uuid


# our start page
@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')


@app.route('/submission', methods=['GET', 'POST'])
@login_required # user needs to be logged in
def submission():

    # display the boreholes
    boreholes = pd.read_csv('app/data/all_BH.csv') # change this to our borehole selection 
    boreholes = list(zip(boreholes["BH_X_LV95"], boreholes["BH_Y_LV95"]))

    # submissions
    submissions = current_user.get_submissions().all()

    # get update -> change this
    for submission in submissions:
        submission.get_progress()

    return render_template('submission.html', title='Home', boreholes=boreholes, submissions=submissions)


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

        # create output directory for user (this)
        try:
            os.mkdir(os.path.join(app.config["OUTPUT_DIR"], str(user.id))) 
        except Exception as e:
            print("Could not create directory for user {}!".format(d))
            print(e)

        # we can commit
        db.session.commit()

        # we can log the user in
        login_user(user, remember=False)
        
        return redirect(url_for('index')) # we should log him 

    # otherwise send registration form
    return render_template('register.html', title='Register', form=form)


def get_model_request(request):
    coordinates = json.loads(request.form['coordinates'])

    name = request.form["name"]

    spacing = (int(request.form["sx"]), 
                int(request.form["sy"]), 
                int(request.form["sz"]) )

    depth = (int(request.form["oz"]), 
            int(request.form["z1"]) )

    realizations = (int(request.form["nu"]), 
                    int(request.form["nf"]), 
                    int(request.form["np"]))

    return coordinates, name, spacing, depth, realizations


# submit job
@app.route('/model', methods=['GET', 'POST'])
@login_required # user needs to be logged in
def model():

    if request.method=="POST":

        # get data
        coordinates, name, spacing, depth, realizations = get_model_request(request)

        # values for job
        job_id = str(uuid.uuid1()) # unique identifier for job
        working_dir = os.path.join(app.config["OUTPUT_DIR"], str(current_user.id), job_id) # saving directory

        # check values before
        valid, msg = False, ""
        if len(coordinates) == 0:
            flash('Invalid inputs')
            return url_for('submission')
        else: 
            valid = True

        # we submit the job
        if valid:
            
            # get the job into queue 
            job = Job.create("app.tasks.run_model", id=job_id, args=(job_id, working_dir, coordinates, spacing, depth, realizations), connection=app.redis, timeout=app.config["JOB_TIMEOUT"])

            # show in job submission
            submission = Submission(id=job_id, name=name, user_id=current_user.id)
            db.session.add(submission)
            db.session.commit()

            # submit
            rq_job = app.task_queue.enqueue_job(job)

            flash('Job {} was submited'.format(submission.id))
            return url_for('submission')
        else:
            msg = "Input error"
            flash('Job could not be submited: {}'.format(msg))
            return url_for('index')  # + "#interactiveMapSection"

    else:
        flash('Could not submit model!')
        return url_for('index')
    

# views the result of a job
@app.route('/view', methods=['GET'])
@login_required # user needs to be logged in
def view():

    # get the submission id
    submission_id = request.args.get('id', None)

    # get the realization id 
    realization_id = int(request.args.get('realization_id', 0))

    # find submission
    submission = Submission.query.filter_by(id=submission_id).first()

    # check if submission is valid and from the same user
    if submission is not None and submission.user_id==current_user.id: #and submission.complete:

        # we can view the results
        out_dir = os.path.join(app.config["OUTPUT_DIR"], str(current_user.id), str(submission.id), "realizations.npy") 
        realizations = np.load(out_dir)

        # choose realizations
        d = realizations.shape[0]
        realization_id = max(0, min(realization_id, d-1)) # avoids errros
        realization = realizations[realization_id] 

        # generate visualization and return it
        html = generate_visualization(realization)
        return render_template('view.html', plot=html, submission=submission, realization_id=realization_id ,realizations=d)
    else:
        # we could add an error for each error type
        flash('Submission {} cannot be viewed'.format(submission_id))

    return redirect(url_for('submission'))


# download realization
@app.route('/download', methods=['GET'])
@login_required # user needs to be logged in
def download():

    # get the submission id
    submission_id = request.args.get('id', None)

    # find submission
    submission = Submission.query.filter_by(id=submission_id).first()

    # check if submission is valid and from the same user
    if submission is not None and submission.user_id==current_user.id and submission.complete:

        # we can view the results
        path = os.path.join(app.config["OUTPUT_DIR"], str(current_user.id), str(submission.id), "realizations.npy") 
        return send_file(path, as_attachment=True)

    else:
        # we could add an error for each error type
        flash('Submission {} cannot be downloaded'.format(submission_id))

    return redirect(url_for('submission'))



# deletes a submission
@app.route('/delete', methods=['GET'])
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
        out_dir = os.path.join(app.config["OUTPUT_DIR"], str(current_user.id), str(submission.id))
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)

        flash('Submission {} was deleted'.format(submission_id))
    else:
        flash('Submission {} could not be deleted'.format(submission_id))

    return redirect(url_for('submission'))
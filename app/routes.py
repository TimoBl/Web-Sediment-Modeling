from flask import render_template, flash, redirect, url_for, send_file
from app import app, db
from app.models import User, Submission
from app.forms import LoginForm, RegistrationForm, JobSubmissionForm
from flask import request
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required
import os
from rq.job import Job
from flask_bootstrap import Bootstrap

# for developpemnt only -> we will have to clean up
import numpy as np
import shutil
import plotly
import plotly.graph_objects as go
import plotly.express as px
from rq import Callback
from scipy.interpolate import RegularGridInterpolator as rgi
import json
import pandas as pd
import app.tasks as tasks
from app.tasks import pre_process, run_model, meters_to_coordinates, coordinates_to_meters
import uuid


# global variables
JOB_TIMEOUT = 10*60 # maximum of 10 minutes for job to complete


@app.route('/')
@app.route('/index')
def index():

    # display the boreholes
    boreholes = pd.read_csv('data/all_BH.csv') # change this to our borehole selection 
    coordinates = [meters_to_coordinates(x, y) for x, y in zip(boreholes["BH_X_LV95"], boreholes["BH_Y_LV95"])]

    return render_template('index.html', title='Home', boreholes=coordinates)


@app.route('/submission', methods=['GET', 'POST'])
@login_required # user needs to be logged in
def submission():
    submissions = current_user.get_submissions().all()
    return render_template('submission.html', title='Home', submissions=submissions)


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

    if request.method=="POST":

        # get the coordinates
        coordinates = json.loads(request.form['coordinates'])
        coordinates = np.array([coordinates_to_meters(cor["lat"], cor["lng"]) for cor in coordinates[0]])
        
        # mock values
        name = "Demo"
        spacing = (25, 25, 10) # (25, 25, 5)
        depth = (450, 560) # origin to depth
        job_id = str(uuid.uuid1()) # unique identifier for job
        working_dir = os.path.join("output", str(current_user.id), job_id) # saving directory

        coordinates = np.load("data/polygon_coord_6.npy")[0]

        # check values before
        if len(coordinates) == 0:
            flash('Invalid inputs')
            return url_for('index') #+ "#interactiveMapSection"

        # pre-process 
        valid, msg = pre_process(coordinates, working_dir)

        if valid:
            
            # get the job into queue 
            job = Job.create("tasks.run_model", args=(current_user.id, job_id, working_dir, name, spacing, depth), id=job_id, connection=app.redis, timeout=JOB_TIMEOUT)

            # show in job submission
            submission = Submission(id=job_id, name=name, user_id=current_user.id)
            db.session.add(submission)
            db.session.commit()

            # submit
            rq_job = app.task_queue.enqueue_job(job) 


            flash('Job {} was submited') #.format(submission.id))
            return url_for('submission')
        else:
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
        out_dir = os.path.join("output", str(current_user.id), str(submission.id), "realizations.npy") 
        realizations = np.load(out_dir)

        # choose realizations
        (d, x, y, z) = realizations.shape
        realization_id = min(realization_id, d-1)
        realizations = realizations[realization_id] 

        # reshape array to indixes
        X, Y, Z = np.mgrid[0:x, 0:y, 0:z]
        values = realizations
        X, Y, Z, values = X.flatten(), Y.flatten(), Z.flatten(), values.flatten()

        #[X, Y, Z, values] = realizations
        # maybe add a display size

        fig = go.Figure(data=go.Volume(
            x=Z,
            y=Y,
            z=-X,
            value=values,
            opacity=0.3, # needs to be small to see through all surfaces
            surface_count=5, # needs to be a large number for good volume rendering -> we reduced to get better performance
            ))

        fig.update_layout(autosize=True, margin=dict(l=20, r=20, t=20, b=20))
        
        # maybe we should then get the html width somehow
        html = plotly.io.to_html(fig, full_html=False, default_height=500, default_width=700)  # you should interactively get the width before from the client, and maybe also have the possibility to change it 
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
        path = os.path.join("output", str(current_user.id), str(submission.id), "realizations.npy") 
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
        out_dir = os.path.join("output", str(current_user.id), str(submission.id))
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)

        flash('Submission {} was deleted'.format(submission_id))
    else:
        flash('Submission {} could not be deleted'.format(submission_id))

    return redirect(url_for('submission'))
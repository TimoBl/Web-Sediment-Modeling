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
import plotly
import plotly.graph_objects as go
import plotly.express as px
import json
import pandas as pd
import app.tasks as tasks
from app.tasks import run_model
import uuid


# global variables
JOB_TIMEOUT = 10*60 # maximum of 10 minutes for job to complete


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')


@app.route('/notifications')
@login_required
def notifications():
    # submissions
    submissions = current_user.get_submissions().all()

    # get update -> change this
    # for submission in submissions:
    #    submission.get_progress()

    return [{'name': sub.name, 'time': sub.timestamp, 'status': sub.status, 'complete': sub.complete} for sub in submissions]

@app.route('/submission', methods=['GET', 'POST'])
@login_required # user needs to be logged in
def submission():

    # display the boreholes
    boreholes = pd.read_csv('data/all_BH.csv') # change this to our borehole selection 
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


def get_model_request(request):
    coordinates = json.loads(request.form['coordinates'])
    #coordinates = np.array([coordinates_to_meters(cor["lat"], cor["lng"]) for cor in coordinates[0]])

    name = request.form["name"] 
    name = name if name != "NaN" else "Test"

    sx, sy, sz = request.form["sx"], request.form["sy"], request.form["sz"]
    spacing = (
        int(sy) if sx != "NaN" else 25,
        int(sy) if sy != "NaN" else 25,
        int(sz) if sz != "NaN" else 1,
    )

    oz, z1 = request.form["oz"], request.form["z1"]
    depth = (
        int(oz) if oz != "NaN" else 450,
        int(z1) if z1 != "NaN" else 560,
    )

    #nreal_units, nreal_facies, nreal_prop = request.form["nreal_units"], request.form["nreal_units"], request.form["nreal_prop"] 
    realizations = (1, 1, 1)

    return coordinates, name, spacing, depth, realizations


# submit job
@app.route('/model', methods=['GET', 'POST'])
@login_required # user needs to be logged in
def model():

    if request.method=="POST":

        # get data
        coordinates, name, spacing, depth, realizations = get_model_request(request)
        #coordinates = np.load("data/polygon_coord_6.npy")
        print(coordinates)

        # values for job
        job_id = str(uuid.uuid1()) # unique identifier for job
        working_dir = os.path.join("output", str(current_user.id), job_id) # saving directory

        # check values before
        if len(coordinates) == 0:
            flash('Invalid inputs')
            return url_for('index') #+ "#interactiveMapSection"

        # pre-process 
        #valid, msg = pre_process(coordinates, working_dir)

        valid, msg = True, "Test"
        if valid:
            
            # get the job into queue 
            job = Job.create("tasks.run_model", args=(job_id, working_dir, coordinates, spacing, depth, realizations), id=job_id, connection=app.redis, timeout=JOB_TIMEOUT)

            # show in job submission
            submission = Submission(id=job_id, name=name, user_id=current_user.id)
            db.session.add(submission)
            db.session.commit()

            # submit
            rq_job = app.task_queue.enqueue_job(job) 


            flash('Job {} was submited'.format(submission.id))
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

        # identify colorscale for the figures, goes from rane 0 to 1, as 0 is not going to be shown, the color doesn't matter but it is nice to point it out
        colorscales = [[0,'white'],[0.1, 'red'], [0.2,'blue'],[0.3,'green'],[0.4,'darkgoldenrod'], [0.5, 'lightgreen'], [0.6,'yellow'],[0.7,'black']]

        #[X, Y, Z, values] = realizations
        # maybe add a display size


        ####### computation for whole figure, iso surface can plot contour of volume
        fig = go.Figure(data=go.Isosurface(
            x=Z,
            y=Y,
            z=-X,
            value=values,
            isomin=1,  # indicate range min of "color scale" so 0 value not taken in account
            isomax=7, # indicate range max of "color scale"
            opacity=0.3, # needs to be small to see through all surfaces
            colorscale=colorscales, # assign color scale with the custom one
            opacityscale=[[0, 0], [1/13, 1], [1, 1]]), #input range to remove the 0 as colorization , redundancy with isomin, but safety measure
            caps=dict(x_show=False, y_show=False), # remove the color coded surfaces on the sides of the visualisation domain for clearer visualization
            #surface_count=5, # needs to be a large number for good volume rendering -> we reduced to get better performance
            ))

        fig.update_layout(autosize=True, margin=dict(l=20, r=20, t=20, b=20))


        ####### creating slices for z axis

        nb_frames0 = values.shape[2]

        fig0 = go.Figure(frames=[go.Frame(data=go.Surface(
            z=(k) * np.ones(values[:,:,k].shape),   # create surface based on k-th element of z slice, because animation or slider based
            surfacecolor=values[:,:,k],     #create color code surface based on k-th element of z slice, because animation or slider based
            cmin=1, cmax=7,     #for surface, indicate the minimum color and maximum, like iso for volume
            colorscale=colorscales, # assign color scale with the custom one
            opacityscale=[[0, 0], [1/13, 1], [1, 1]]),  #input range to remove the 0 as colorization , redundancy with isomin, but safety measure
            name=str(k) # you need to name the frame for the animation to behave properly
            )
            for k in range(nb_frames0)])

        # Add data to be displayed before animation starts
        fig0.add_trace(go.Surface(
            z=0 * np.ones(values[:,:,0].shape), # create surface based on first element of z slice
            surfacecolor=values[:,:,0], #create color code surface based on first element of z slice
            colorscale=colorscales, # assign color scale with the custom one
            cmin=1, cmax=7,    #for surface, indicate the minimum color and maximum, like iso for volume
            #colorbar=dict(thickness=20, ticklen=4)
            ))

        # define the animation transition, will also be used for the second slider
        def frame_args(duration):
            return {
                    "frame": {"duration": duration},
                    "mode": "immediate",
                    "fromcurrent": True,
                    "transition": {"duration": duration, "easing": "linear"},
                }
        #create slider
        sliders = [
                    {
                        "pad": {"b": 10, "t": 20},
                        "len": 0.9,
                        "x": 0.1,
                        "y": 0,
                        "currentvalue": {           # put current value as number above the slider force color font
                                "offset": 20,
                                "xanchor": "center",
                                "font": {
                                  "color": '#888',
                                  "size": 15
                                }
                              },
                        "font": {"color": 'white'}, # remove ticks because too many labels, put is same as the background
                        "steps": [
                            {
                                "args": [[f.name], frame_args(0)],
                                "label": str(k),
                                "method": "animate",
                            }
                            for k, f in enumerate(fig0.frames)
                        ],
                    }
                ]

        # Layout
        fig0.update_layout(
                 title="slice z",
                 scene = dict(
                    aspectratio=dict(x=1, y=1, z=1),    # make the 3 axis of same ratio and step aspect
                    xaxis = dict(visible=False),    # remove grid and axis label of x
                    yaxis = dict(visible=False),    # remove grid and axis label of y
                    zaxis=dict(visible=False),      # remove grid and axis label of z
                    camera = dict(      # set camera layout to top view to better read the frame, rotate based on y to have the good orientation
                        eye=dict(x=0, y=0.5, z=2.0)
                    )
                 ),
                 updatemenus = [
                    {
                        "buttons": [
                            {
                                "args": [None, frame_args(50)],
                                "label": "&#9654;", # play symbol
                                "method": "animate",
                            },
                            {
                                "args": [[None], frame_args(0)],
                                "label": "&#9724;", # pause symbol
                                "method": "animate",
                            },
                        ],
                        "direction": "left",
                        "pad": {"r": 10, "t": 70},
                        "type": "buttons",
                        "x": 0.1,
                        "y": 0,
                    }
                 ],
                 sliders=sliders
        )

        ####### creating slice for y axis

        nb_frames = values.shape[1]

        fig1 = go.Figure(frames=[go.Frame(data=go.Surface(
            z=(k) * np.ones(values[:,k,:].shape),   # create surface based on k-th element of y slice, because animation or slider based
            surfacecolor=values[:,k,:],         #create color code surface based on k-th element of y slice, because animation or slider based
            cmin=1, cmax=7,     #for surface, indicate the minimum color and maximum, like iso for volume
            colorscale=colorscales, # assign color scale with the custom one
            opacityscale=[[0, 0], [1/13, 1], [1, 1]]),  #input range to remove the 0 as colorization , redundancy with isomin, but safety measure
            name=str(k) # you need to name the frame for the animation to behave properly
            )
            for k in range(nb_frames)])

        # Add data to be displayed before animation starts
        fig1.add_trace(go.Surface(
            z=0 * np.ones(values[:,0,:].shape), # create surface based on first element of y slice
            surfacecolor=values[:,0,:],  #create color code surface based on first element of y slice
            colorscale=colorscales, # assign color scale with the custom one
            cmin=1, cmax=7,    #for surface, indicate the minimum color and maximum, like iso for volume
            #colorbar=dict(thickness=20, ticklen=4)
            ))

        # create slider for figure 1
        sliders = [
                    {
                        "pad": {"b": 10, "t": 20},
                        "len": 1.0,
                        "x": 0.1,
                        "y": 0,
                        "currentvalue": {           # put current value as number above the slider force color font
                                "offset": 20,
                                "xanchor": "center",
                                "font": {
                                  "color": '#888',
                                  "size": 15
                                }
                              },
                        "font": {"color": 'white'}, # remove ticks because too many labels, put is same as the background
                        "steps": [
                            {
                                "args": [[f.name], frame_args(0)],
                                "label": str(k),
                                "method": "animate",
                            }
                            for k, f in enumerate(fig1.frames)
                        ],
                    }
                ]

        # Layout for figure 1
        fig1.update_layout(
                 title="slice y",
                 scene = dict(
                    aspectratio=dict(x=1, y=1, z=1),    # make the 3 axis of same ratio and step aspect
                    xaxis = dict(visible=False),    # remove grid and axis label of x
                    yaxis = dict(visible=False),    # remove grid and axis label of y
                    zaxis=dict(visible=False),      # remove grid and axis label of z
                    camera = dict(      # set camera layout to top view to better read the frame, rotate based on y to have the good orientation
                        eye=dict(x=0, y=0.5, z=2.0)
                    )
                 ),
                 updatemenus = [
                    {
                        "buttons": [
                            {
                                "args": [None, frame_args(50)],
                                "label": "&#9654;", # play symbol
                                "method": "animate",
                            },
                            {
                                "args": [[None], frame_args(0)],
                                "label": "&#9724;", # pause symbol
                                "method": "animate",
                            },
                        ],
                        "direction": "left",
                        "pad": {"r": 10, "t": 70},
                        "type": "buttons",
                        "x": 0.1,
                        "y": 0,
                    }
                 ],
                 sliders=sliders
        )

        # store in the html 3 separated figures in a row (not as subplot) because they need their own interaction, no h and w definition as it will be full in the iFrame and handle as div in main bootstrap
        with open('view.html', 'w', encoding="utf-8") as html:
            html.writelines(plotly.io.to_html(fig, include_plotlyjs='cnd', full_html=True))
            html.writelines(plotly.io.to_html(fig0, include_plotlyjs='cnd', full_html=True))
            html.writelines(plotly.io.to_html(fig1, include_plotlyjs='cnd', full_html=True))
        
        # maybe we should then get the html width somehow
        #html = plotly.io.to_html(fig, full_html=False, default_height=500, default_width=700)  # you should interactively get the width before from the client, and maybe also have the possibility to change it
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
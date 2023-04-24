from flask import render_template, flash, redirect, url_for
from app import app, db
from app.models import User, Submission
from app.forms import LoginForm, RegistrationForm, JobSubmissionForm
from flask import request
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user, login_required


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
        rq_job = app.task_queue.enqueue('app.tasks.run_geo_model', name, dim, spacing)

        print(rq_job)

        # show job submission
        submission = Submission(id=rq_job.get_id(), name=form.name.data, user_id=current_user.id)
        db.session.add(submission)
        db.session.commit()

        print(submission.get_rq_job())
        
        return redirect(url_for('index'))

    return render_template('model.html', title='Model', form=form)#, user=user) #str(m.get_units_domains_realizations())



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
        db.session.delete(submission)
        db.session.commit()
        flash('Submission {} was deleted'.format(submission_id))
    else:
        flash('Submission {} could not be deleted'.format(submission_id))

    return redirect(url_for('index'))
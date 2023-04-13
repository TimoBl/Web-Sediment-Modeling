from flask import render_template
from app import app
from app.model import GeoModel

@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Timo'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', user=user, posts=posts)


@app.route('/model')
def model():
    m = GeoModel()
    
    # with three levels of simulation
    m.compute_surf(2)
    m.compute_facies(2)
    m.compute_prop(1)

    return str(m.get_units_domains_realizations())
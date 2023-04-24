# this file will handle async computations
from model import GeoModel
import os

# this is the function we will call with redis
def run_geo_model(name, dim, spacing):

    try:
        m = GeoModel(name, dim, spacing)
        
        # with three levels of simulation
        m.compute_surf(2)
        #m.compute_facies(1)
        #m.compute_prop(1)

    except:
        print("error")

    finally:
        _set_submission_status(1) # finished executing


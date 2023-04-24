# this file will handle async computations
from model import GeoModel
from rq import get_current_job
import os

# this is the function we will call with redis
def run_geo_model(name, dim, spacing):

    try:
        m = GeoModel(name, dim, spacing)
        
        _set_submission_status(0) # beginning

        # with three levels of simulation
        m.compute_surf(2)
        #m.compute_facies(1)
        #m.compute_prop(1)

    except:
        print("error")

    finally:
        _set_submission_status(1) # finished executing


# we set the status
def _set_submission_status(status):
    job = get_current_job()

    if job:
        job.meta['status'] = status
        job.save_meta()
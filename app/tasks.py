# this file will handle async computations
from model import GeoModel
from rq import get_current_job
import os

# this is the function we will call with redis
def run_geo_model(name, dim, spacing):

    try:
        m = GeoModel(name, dim, spacing)
        
        _set_progress_status("0%", False) # beginning

        # with three levels of simulation
        m.compute_surf(2)
        #m.compute_facies(1)
        #m.compute_prop(1)

        _set_progress_status("100%", True) # finished executing

    except:
        # we should implement verfication status
        print("error")

    finally:
        # is always excuted regardless of execution
        print("end")


# we set the status
def _set_progress_status(status, complete):
    job = get_current_job()

    if job:
        # set status
        job.meta['status'] = status
        job.meta['complete'] = complete
        job.save_meta()
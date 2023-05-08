# this file will handle async computations
from model import GeoModel, AareModel
from rq import get_current_job
import os
import ArchPy 
import numpy as np


# this is the function we will call with redis
def run_geo_model(user_id, name, dim, spacing):

    try:

        # beginning computation
        job =_set_progress_status("0%", False)

        # create output dir
        out_dir = os.path.join("output", str(user_id), str(job.id)) # maybe add output directory as global function
        if not os.path.exists(out_dir):
            os.mkdir(out_dir) # somehow archpy overwrite this when we give directory

        # create geological model
        model = GeoModel(name, dim, spacing, working_directory=out_dir)
        
        # with three levels of simulation
        model.compute_surf(1)
        model.compute_facies(1)
        model.compute_prop(1)

        # save output
        realizations = model.get_units_domains_realizations()
        np.save(os.path.join(out_dir, "realizations.npy"), realizations)

    except Exception as e:
        # we should implement verfication status
        print("Error: ", e)

    finally:
        # is always excuted regardless of execution
        print("end")

    # job completed successfully
    _set_progress_status("100%", True)



def run_aare_model(user_id, name, dim, spacing):

    try:

        # beginning computation
        job =_set_progress_status("0%", False)

        # create output dir
        out_dir = os.path.join("output", str(user_id), str(job.id)) # maybe add output directory as global function
        if not os.path.exists(out_dir):
            os.mkdir(out_dir) # somehow archpy overwrite this when we give directory

        # run geological model
        realizations = AareModel(spacing=spacing)

        # the more efficient representation does not lead to better view
        #X, Y, Z = np.nonzero(realizations[0])
        #V = realizations[0, X, Y, Z]
        #realizations = np.array([X, Y, Z, V])

        # save output
        np.save(os.path.join(out_dir, "realizations.npy"), realizations)

    except Exception as e:
        # we should implement verfication status
        print("Error: ", e)

    finally:
        # is always excuted regardless of execution
        print("end")

    # job completed successfully
    _set_progress_status("100%", True)






# we set the status
def _set_progress_status(status, complete):
    job = get_current_job()

    if job:
        # set status
        job.meta['status'] = status
        job.meta['complete'] = complete
        job.save_meta()

    return job
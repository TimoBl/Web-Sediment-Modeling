# this file will handle async computations
from model import GeoModel, AareModel
from rq import get_current_job
import os
import ArchPy 
import numpy as np

'''
# this is the function we will call with redis
def run_geo_model(user_id, name, dim, spacing):

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
'''


# a naive approach of 
def coordinates_to_meters(lat, lng):
    N = (111132.954 * lat) / 2
    E = 2 * (111319.488 * np.cos(np.pi *lat / 180)) * lng
    return [N, E]


def run_aare_model(user_id, name, coordinates, spacing):

    try:

        # beginning computation
        job =_set_progress_status("0%", False)

        # create output dir
        out_dir = os.path.join("output", str(user_id), str(job.id)) # maybe add output directory as global function
        if not os.path.exists(out_dir):
            os.mkdir(out_dir) # somehow archpy overwrite this when we give directory

        # convert coordinates
        poly_data = [[coordinates_to_meters(p['lat'], p['lng']) for p in coordinates[0]]]
        #print(poly_data)

        #poly_data = np.load("data/polygon_coord_6.npy") 
        #print(poly_data)

        # run geological model
        realizations = AareModel(poly_data, spacing)

        # the more efficient representation does not lead to better view
        #X, Y, Z = np.nonzero(realizations[0])
        #V = realizations[0, X, Y, Z]
        #realizations = np.array([X, Y, Z, V])

        # save output
        np.save(os.path.join(out_dir, "realizations.npy"), realizations)

        # job completed successfully
        _set_progress_status("100%", True)

    except Exception as e:

        # we should implement verfication status
        print("Error: ", e)

        # job did not completed successfully
        _set_progress_status("100%", False)

    finally:
        # is always excuted regardless of execution
        print("End")

    






# we set the status
def _set_progress_status(status, complete):
    job = get_current_job()

    if job:
        # set status
        job.meta['status'] = status
        job.meta['complete'] = complete
        job.save_meta()

    return job
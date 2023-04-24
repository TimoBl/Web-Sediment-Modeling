# this file will handle async computations
from app.model import GeoModel


# this is the function we will call with redis

def run_geo_model(self, name, dim, spacing):
    try:
        print(name)

        m = GeoModel(name, dim, spacing)
        
        # with three levels of simulation
        #m.compute_surf(2)
        #m.compute_facies(1)
        #m.compute_prop(1)

        os.mkdir("test")

    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    
    finally:
        _set_task_progress(100)
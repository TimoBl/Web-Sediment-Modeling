# this file will handle async computations
from app.model import GeoModel


def run_geo_model(self, name, dim, spacing):
    print(name)

    m = GeoModel(name, dim, spacing)
    
    # with three levels of simulation
    #m.compute_surf(2)
    #m.compute_facies(1)
    #m.compute_prop(1)
    print(m)

    return "finished"
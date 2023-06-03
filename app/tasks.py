# this file will handle async computations
from rq import get_current_job
import os
import ArchPy 
import numpy as np
import geone
import geone.covModel as gcm
import os
import sys
from ArchPy.base import *
import pandas as pd
import shapely
import shutil
from shapely.geometry import Polygon, MultiPolygon, Point
#from app.models import Submission
#from app import db


#dictionary of units
dic_s_names_grouped = {'"Alte Seetone"':"Alte Seetone",
              "Bachschutt / Bachschuttkegel (undifferenziert)":"Hangschutt_Bachschutt",
              "Deckschicht":"SUP",
              "Hangschutt / Hanglehm (undifferenziert)":"Hangschutt_Bachschutt",
              "Interglaziale Seetone (Eemzeitliche Seetone)":"IGT",
              "Künstliche Auffüllung etc. (anthropogener Horizont, undifferenziert)":"SUP",
              "Moräne der Letzten Vergletscherung":"LGM",
              'Moräne der Vorletzten Vergletscherung ("Altmoräne")':"Altmorane",
              "Oppligen-Sand":"Oppligen-Sand",
              'Rückzugsschotter der Letzten Vergletscherung ("Felderschotter" und Äquivalente)':"LGMT",
              'Spät- bis postglaziale Schotter':"LGA",
              'Spät- bis postglaziale Stausedimente und Seeablagerungen (undifferenziert)':"LGL",
              'Spätglaziale Moräne (undifferenziert)':"LGMT",
              'Subrezente bis rezente Alluvionen (Fluss- und Bachschotter, Überschwemmungssediment, undifferenziert)':"YG",
              'Uttigen-Bümberg-Steghalde-Schotter':"Bumberg",
              'Alte Deltaschotter im Belpmoos':"Bumberg",
              'Verlandungssedimente, Sumpf, Ried':"SUP",
              'Vorletzteiszeitliche glaziolakustrische Ablagerungen und Schlammmoräne':"glacio_lac + schlamm",
              'Vorstossschotter der Letzten Vergletscherung (vorwiegend Münsingen- u. Karlsruhe-Schotter)':"Munsingen",
              'Rückzugsschotter der Vorletzten Vergletscherung, Kies-Sand-Komplex von Kleinhöchstetten':"Altmorane"}


dic_facies = {
           "OH":"others","OL":"others",'kunst':"others",'Pt':"others", 'Bl':"others","st":"others","St-Bl":"others","KA":"others",
           "S-SM":"Sand","S": "Sand","SP-SM":"Sand","SP":"Sand","SW":"Sand","S-SC":"Sand","SP-SC":"Sand","SW-SM":"Sand",
           "SM":"Clayey sand","SC":"Clayey sand","SC-SM":"Clayey sand",
           "GM":"Clayey gravel","GC":"Clayey gravel","GC-GM":"Clayey gravel",
           "G":"Gravel","G-GM":"Gravel","GW-GM":"Gravel","GP-GM":"Gravel","GP":"Gravel","GW":"Gravel","GP-GC":"Gravel","G-GC":"Gravel","GP-gM":"Gravel","GW-GC":"Gravel",
           "ML" : "Clay and silt", "CL-ML":"Clay and silt","CL":"Clay and silt","CM":"Clay and silt","CH":"Clay and silt",
           'FELS':"Bedrock"}



# a naive approach of coordinate transformation (should be replaced!!!)
def coordinates_to_meters(lat, lng):
    N = (111132.954 * lat) / 2
    E = 2 * (111319.488 * np.cos(np.pi * lat / 180)) * lng
    return [N, E]

def meters_to_coordinates(N, E):
    lat = 2 * N / 111132.954 
    lng = E / (2 * 111319.488 * np.cos(np.pi * lat / 180))
    return [lat, lng]



# pre-processing of the data for computation (# first part)
# ! there seems to be some problems with the code of ArchPy, so we currently disable the automatic update !
def initialize_data(data_dir="data"):

    # load the data
    poly_data = np.load(os.path.join(data_dir, "polygon_coord_3.npy"))  # the maximum extent of the zone
    lay = pd.read_csv(os.path.join(data_dir, "Layer_all_free.csv"), error_bad_lines=False, sep=";", low_memory=False)
    bhs = pd.read_csv(os.path.join(data_dir, "all_BH.csv"))

    # initialize project
    model = ArchPy.inputs.import_project("Aar_geomodel", ws=data_dir, 
            import_bhs=False, import_grid=False, import_results=False)  # load the yaml file

    # define zone
    zone = MultiPolygon([Polygon(p) for p in poly_data])
    
    bhs_points = []
    for i, (ix, iy) in enumerate(zip(bhs.BH_X_LV95, bhs.BH_Y_LV95)):
        p = shapely.geometry.Point(ix, iy)
        p.name = i
        bhs_points.append(p)

    # check intersection
    l = [p.name for p in bhs_points if p.intersects(zone)]

    # select zone
    bhs_sel = bhs.loc[np.array(l)]
    lay_sel = lay[lay["BH_GEOQUAT_ID"].isin(bhs_sel["BH_GEOQUAT_ID"])]

    # import geological database 
    db, list_bhs = load_bh_files(bhs_sel, lay_sel.reset_index(), lay_sel.reset_index(),
        lbhs_bh_id_col="BH_GEOQUAT_ID", u_bh_id_col="BH_GEOQUAT_ID", fa_bh_id_col="BH_GEOQUAT_ID",
        u_top_col = "LA_TOP_m",u_bot_col = "LA_BOT_m",u_ID = "LA_Lithostrati",
        fa_top_col = "LA_TOP_m",fa_bot_col = "LA_BOT_m",fa_ID = "LA_USCS_IP_1",
        bhx_col='BH_X_LV95', bhy_col='BH_Y_LV95', bhz_col='BH_Z_Alt_m', bh_depth_col='BH_TD_m',
        dic_units_names = dic_s_names_grouped, dic_facies_names = dic_facies, altitude = False)

    # adding boreholes
    all_boreholes = extract_bhs(db, list_bhs, model, 
        units_to_ignore=('Keine Angaben', 'Raintal-Deltaschotter', 'Hani-Deltaschotter', 'Fels'),
        facies_to_ignore=('Bedrock', 'asfd'))

    # save for reuse in computation
    with open(os.path.join(data_dir, "boreholes"), "wb") as f:
        pickle.dump(all_boreholes, f)



# pre-process the data and checks before starting computation
def pre_process(polygon, working_dir, data_dir="data"):

    # load boreholes
    with open(os.path.join(data_dir, "boreholes"), "rb") as f:
        all_boreholes = pickle.load(f)

    # convert coordinates
    poly = Polygon(polygon)

    # convert boreholes
    bhs_points = []
    for i, ibh in enumerate(all_boreholes):
        p = shapely.geometry.Point(ibh.x, ibh.y)
        p.name = i
        bhs_points.append(p)

    #polygon = np.load("data/polygon_coord_6.npy") poly = Polygon(polygon[0])  # create a polygon object with shapely

    # check intersection
    l = np.array([p.name for p in bhs_points if p.intersects(poly)])
    
    # must have at least 3 boreholes
    if len(l) >= 3:

        # we can save our things into the working directory
        if not os.path.exists(working_dir):
            os.mkdir(working_dir)

        # our borehole sample
        boreholes_sel = np.array(all_boreholes)[np.array(l)]
        with open(os.path.join(working_dir, "boreholes"), "wb") as f:
            pickle.dump(boreholes_sel, f)

        # our polygon input
        np.save(os.path.join(working_dir, "polygon.npy"), polygon)

        # currently we don't allow yaml changing, but we will copy a default file 
        shutil.copyfile(os.path.join(data_dir, "Aar_geomodel.yaml"), os.path.join(working_dir, "settings.yaml"))

        return True, "Valid Input"
    else:
        return False, "Only {} boreholes in selection".format(len(l))


'''
# Analyze boreholes
def borehole_analysis(ArchTable, db, list_facies,
                     Strat_ID = "Strat_ID", Facies_ID = "Facies_ID",
                     top_col = "top", bot_col = "bot", facies_thresh=0.05, plot=True, plot_dir=None):
                     
    """
    Function to analyse geological database (db) and link facies to units
    """
    
    t = db.copy()
    
    # Units
    # only keep units that appears in db
    for unit in ArchTable.get_all_units():
        if unit.name not in db.Strat_ID.unique():
            for pile in ArchTable.get_piles():
                pile.remove_unit(unit)

    # Facies
    t["thickness"] = t[top_col] - t[bot_col]
    threshold = facies_thresh # proportion threshold to accept a facies in a unit

    for unit in t[Strat_ID].unique():
        print("\n\n###" +unit+"####\n")
        df = pd.DataFrame(t.groupby([Strat_ID, Facies_ID])["thickness"].sum()).loc[unit] #facies prop in unit
        df = (df / df.sum(0)).round(2)
        df.sort_values(ascending=False,by="thickness",inplace=True)

        for idx in df[df["thickness"]>threshold].index:
            for i in range(len(list_facies)):
                if idx == list_facies[i].name:
                    if ArchTable.get_unit(unit) is not None:
                        ArchTable.get_unit(unit).add_facies(list_facies[i])
'''


# Fixing this issue:
#### Here I had a little problem with the instances of the units because the units objects in the boreholes are not the same that the one in the Arch_table (because they have been saved and loaded with pickle). This causes issue with ArchPy code so I had to remove all the units from the Arch_table and re-add them but with the instance of the boreholes
def filter_units(model, boreholes_sel):
    stratis_unique = []
    for bh in boreholes_sel:
        if bh.log_strati is not None:
            for s in bh.get_list_stratis():
                if s not in stratis_unique:
                    stratis_unique.append(s)
      
    # fix the issue with the instance of the boreholes
    for u in model.get_all_units():
        model.get_pile_master().remove_unit(u)
        
    for unit in stratis_unique:
        model.get_pile_master().add_unit(unit)


def run_model(user_id, job_id, working_dir, name, spacing, depth, nreal_units=1, nreal_facies=1, nreal_prop=1):

    # beginning computation
    job =_set_progress_status(job_id, "running", True)

    try:
        # load data
        polygon = Polygon(np.load(os.path.join(working_dir, "polygon.npy")))
        with open(os.path.join(working_dir, "boreholes"), "rb") as f:
            boreholes = pickle.load(f)

        # create model
        model = ArchPy.inputs.import_project("settings", ws=working_dir, import_bhs=False, import_grid=False, import_results=False)  # load the yaml file
        filter_units(model, boreholes)

        # create grid
        (sx, sy, sz) = spacing
        (oz, z1) = depth 
        origin = (polygon.bounds[0], polygon.bounds[1], oz)
        dimensions = (  len(np.arange(polygon.bounds[0], polygon.bounds[2]+sx, sx)) - 1,
                        len(np.arange(polygon.bounds[1], polygon.bounds[3]+sy, sy)) - 1,
                        len(np.arange(oz, z1+sz, sz)) - 1   )
        model.add_grid(dimensions, spacing, origin, polygon=polygon, top="data/MNT25.tif", bot="data/BEM25-2021_crop_Aar.tif")

        # add boreholes
        model.add_bh(boreholes)

        # process
        model.process_bhs()
        model.compute_surf(nreal_units)
        model.compute_facies(nreal_facies)
        model.compute_prop(nreal_prop)

        #realizations = np.array([1, 2, 3])

        # save output
        realizations = model.get_units_domains_realizations()
        np.save(os.path.join(working_dir, "realizations.npy"), realizations)

        # finished
        job =_set_progress_status(job_id, "finished", True)

    except Exception as e:

        # finished
        job =_set_progress_status(job_id, "failed", False)

        print(e)
    

# we set the status
def _set_progress_status(job_id, status, complete):
    job = get_current_job()
    #job = Job.fetch(job_id, connection=app.redis)

    if job:
        # set status
        job.meta['status'] = status
        job.meta['complete'] = complete
        job.save_meta()

        # set submission
        #sub = Submission.query.get(job.get_id())
        #sub.status = status
        #sub.complete = complete
        #db.session.commit()


    return job


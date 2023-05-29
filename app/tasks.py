# this file will handle async computations
# from model import GeoModel, AareModel
from rq import get_current_job
import os
import ArchPy 
import numpy as np

import geone
import geone.covModel as gcm
import os
import sys
#import pyvista as pv
from ArchPy.base import *
import pandas as pd
import shapely
from shapely.geometry import Polygon, MultiPolygon, Point




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


# a naive approach of coordinate transformation
def coordinates_to_meters(lat, lng):
    N = (111132.954 * lat) / 2
    E = 2 * (111319.488 * np.cos(np.pi *lat / 180)) * lng
    return [N, E]


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



class AareModel:

    # Class variables
    bhs_path="data/all_BH.csv"
    all_layers="data/Layer_all_free.csv"
    mnt="data/MNT25.tif"
    bdrck_path="data/BEM25-2021_crop_Aar.tif"
    ws="data"

    def __init__(self, name, poly_data, spacing, select_files=False):
        self.name = name

        # get the data
        self.select_data(poly_data)
        
        # get settings
        sx, sy, sz = spacing
        oz=450
        z1=560
        
        xg = np.arange(self.polygon.bounds[0],self.polygon.bounds[2]+sx,sx)
        nx = len(xg)-1
        yg = np.arange(self.polygon.bounds[1],self.polygon.bounds[3]+sy,sy)
        ny = len(yg)-1
        zg = np.arange(oz,z1+sz,sz)
        nz = len(zg)-1

        self.dimensions = (nx, ny, nz)
        self.spacing = (sx, sy, sz)
        self.origin = (self.polygon.bounds[0], self.polygon.bounds[1], oz)


    # loads the databased on selection
    def select_data(self, poly_data):

        # convert coordinates
        poly_data = [[coordinates_to_meters(p["lat"], p["lng"]) for p in poly_data[0]]]
 
        # load data
        lay = pd.read_csv(AareModel.all_layers, error_bad_lines=False, sep=";")
        bhs = pd.read_csv(AareModel.bhs_path)
        
        # extract boreholes points
        bhs_points = []
        for i, (px, py) in enumerate(zip(bhs.BH_X_LV95, bhs.BH_Y_LV95)):
            po = shapely.geometry.Point(px, py)
            po.name = i
            bhs_points.append(po)

        # get polygon and check intersection with boreholes
        self.polygon = MultiPolygon([Polygon(p) for p in poly_data])
        selection = np.array([po.name for po in bhs_points if po.intersects(self.polygon)])

        # select data
        self.bhs_sel = bhs.loc[selection]
        self.lay_sel = lay[lay["BH_GEOQUAT_ID"].isin(self.bhs_sel["BH_GEOQUAT_ID"])]


    # checks if this is a valid model (-> before runing the model)
    def is_valid(self):
        # we might add more constraints 
        if len(self.bhs_sel) > 0:
            return True, len(self.bhs_sel)
        else:
            return False, "No boreholes in selection"


    # runs the simulation model
    def run(self, nreal_units=2, nreal_facies=2, nreal_prop=1):
        T1 = ArchPy.inputs.import_project("Aar_geomodel", ws=AareModel.ws, import_bhs=False, import_grid=False, import_results=False)
        list_facies = T1.get_all_facies()
        T1.rem_all_facies_from_units()
        T1.add_grid(self.dimensions, self.spacing, self.origin, polygon=self.polygon)

        # import geological database 
        db, list_bhs = load_bh_files(self.bhs_sel, self.lay_sel.reset_index(), self.lay_sel.reset_index(),
                                      lbhs_bh_id_col="BH_GEOQUAT_ID", u_bh_id_col="BH_GEOQUAT_ID", fa_bh_id_col="BH_GEOQUAT_ID",
                                      u_top_col="LA_TOP_m",u_bot_col="LA_BOT_m",u_ID="LA_Lithostrati",
                                      fa_top_col="LA_TOP_m",fa_bot_col = "LA_BOT_m",fa_ID ="LA_USCS_IP_1",
                                      bhx_col='BH_X_LV95', bhy_col='BH_Y_LV95', bhz_col='BH_Z_Alt_m', bh_depth_col='BH_TD_m',
                                      dic_units_names = dic_s_names_grouped,
                                      dic_facies_names = dic_facies, altitude = False)
        
        # borehole analysis and remove/add units/facies that appear in the data
        borehole_analysis(T1, db, list_facies)
        
        # adding boreholes
        all_boreholes = extract_bhs(db, list_bhs, T1, units_to_ignore=('Keine Angaben', 'Raintal-Deltaschotter', 'Hani-Deltaschotter', 'Fels'))
        T1.add_bh(all_boreholes)
     
        # process_bhs
        T1.reprocess()
        
        # simulations
        T1.compute_surf(nreal_units)
        T1.compute_facies(nreal_facies)
        T1.compute_prop(nreal_prop)

        return T1.get_units_domains_realizations()



def run_model(user_id, name, poly_data, spacing):

    # beginning computation
    job =_set_progress_status("0%", False)

    # create output dir
    out_dir = os.path.join("output", str(user_id), str(job.id)) # maybe add output directory as global function
    if not os.path.exists(out_dir):
        os.mkdir(out_dir) # somehow archpy overwrite this when we give directory

    # initialize
    model = AareModel(name, poly_data, spacing)

    # run the simulations
    realizations = model.run()
    
    # the more efficient representation does not lead to better view
    #X, Y, Z = np.nonzero(realizations[0])
    #V = realizations[0, X, Y, Z]
    #realizations = np.array([X, Y, Z, V])

    # save output
    np.save(os.path.join(out_dir, "realizations.npy"), realizations)



# we set the status
def _set_progress_status(status, complete):
    job = get_current_job()

    if job:
        # set status
        job.meta['status'] = status
        job.meta['complete'] = complete
        job.save_meta()

    return job



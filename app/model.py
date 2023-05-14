import numpy as np
import matplotlib.pyplot as plt
import geone
import geone.covModel as gcm
import os
import sys
#import pyvista as pv
import ArchPy
from ArchPy.base import *
import pandas as pd
import shapely
from shapely.geometry import Polygon, MultiPolygon, Point


# MOCK CLASSES FOR PROTOTYPING
def get_mock_units():
	#Creation of the top unit C
	covmodel_SIS = gcm.CovModel3D(elem = [("spherical", {"w":2, "r": [20,20,10]}),
	                                      ("exponential", {"w":1, "r": [30,30,10]})])

	dic_facies_c = {"f_method" : "homogenous", #filling method
	                 "f_covmodel" : covmodel_SIS, #SIS covmodels
	                } #dictionnary for the unit filling

	C = ArchPy.base.Unit(name = "C",
	                      order = 1,       #order in pile
	                      color = "lightgreen",  
	                      surface=ArchPy.base.Surface(),  # top surface
	                      ID = 1,
	                      dic_facies=dic_facies_c
	                     ) 


	## B
	#surface B
	covmodel_b = gcm.CovModel2D(elem = [("cubic", {"w":2, "r" : [15,5]})])
	dic_surf_b = {"covmodel" : covmodel_b, "int_method" : "grf_ineq"}
	Sb = ArchPy.base.Surface(name = "Sb", dic_surf=dic_surf_b)

	#dic facies b 
	dic_facies_b = {"f_method" : "SIS", "f_covmodel" : covmodel_SIS, "probability" : [0.7, 0.3]} 

	B = ArchPy.base.Unit(name = "B",
	                      order = 2,   #order in pile
	                      color = "greenyellow", #color
	                      surface=Sb, # top surface
	                      ID = 2,     #ID
	                      dic_facies=dic_facies_b #facies dictionnary
	                     )


	##A
	covmodel_a = gcm.CovModel2D(elem = [("spherical", {"w":1, "r" : [5,5]})])
	dic_surf_a = {"covmodel" : covmodel_b, "int_method" : "grf_ineq"}
	Sa = ArchPy.base.Surface(name = "Sa", dic_surf=dic_surf_a)

	#dic facies a
	dic_facies_a = {"f_method" : "SIS", "f_covmodel" : covmodel_SIS} 

	A = ArchPy.base.Unit(name = "A",
	                      order = 3,   #order in pile
	                      color = "lightcoral", #color
	                      surface=Sa, # top surface
	                      ID = 3,     #ID
	                      dic_facies=dic_facies_a #facies dictionnary
	                     )
	return [C, B, A]

def get_mock_facies():
	Sand = ArchPy.base.Facies(ID = 1, name = "Sand", color = "yellow")
	Clay = ArchPy.base.Facies(ID = 2, name = "Clay", color = "royalblue")
	Gravel = ArchPy.base.Facies(ID = 3, name = "Gravel", color = "palegreen")
	Silt = ArchPy.base.Facies(ID = 4, name = "Silt", color = "goldenrod")
	return [Sand, Clay, Gravel, Silt]

def get_mock_properties(list_facies):
	cm_prop1 = gcm.CovModel3D(elem = [("spherical", {"w":0.1, "r":[10,10,10]}), ("cubic", {"w":0.1, "r":[15,15,15]})])
	cm_prop2 = gcm.CovModel3D(elem = [("cubic", {"w":0.2, "r":[25, 25, 5]})])

	#list_facies = [Sand, Clay, Gravel, Sandy_gravel] #list of the facies to simulate
	list_covmodels = [cm_prop2, cm_prop1, cm_prop2, cm_prop1] #list of 3D covariance models
	means = [-4, -8, -3, -5] #mean property values
	K = ArchPy.base.Prop("K", 
	                     facies=list_facies,
	                     covmodels=list_covmodels,
	                     means=means,
	                     int_method = "sgs",
	                     vmin = -10,
	                     vmax = -2)
	return K


# GLOBAL VARIABLES (this is done once for the whole app not by session)
data_folder = "data/"
db, l_bhs = ArchPy.inputs.load_bh_files(list_bhs=pd.read_csv(os.path.join(data_folder, "IO_exemple.lbh")), 
										units_data=pd.read_csv(os.path.join(data_folder, "IO_exemple.ud")), 
										facies_data=pd.read_csv(os.path.join(data_folder, "IO_exemple.fd")), 
										altitude=True)



## Test Model ##
# much more efficient instead of creating a class which has as an attribute an Arch_table
# we can instead define a child as a table
class GeoModel(ArchPy.base.Arch_table):
	def __init__(self, name, dimensions, spacing, working_directory="working_directory"):
		super().__init__(name=name, working_directory=working_directory, seed=100, verbose=1)

		# define our simulation grid (this would be our parameters we use)
		#dimensions = (50, 50, 50) # number of cells
		#spacing = (1, 1, 0.1) # cell dimension
		origin = (0, 0, 0) # origin of the simulation
		self.add_grid(dimensions, spacing, origin)

		# next steps
		self.define_model()
		self.pre_process()


	def define_model(self):
		# 1. defining a stratigraphic pile
		P1 = ArchPy.base.Pile("Pile_1")
		self.set_Pile_master(P1)

		# 2. defining units and surfaces
		[C, B, A] = get_mock_units()
		P1.add_unit([C, B, A])

		# 3. add faces
		[Sand, Clay, Gravel, Silt] = facies = get_mock_facies()
		C.add_facies(Gravel)
		B.add_facies([Clay, Sand])
		A.add_facies([Sand, Gravel, Silt])

		# 4. adding properties
		K = get_mock_properties(facies)
		self.add_prop(K)


	def pre_process(self):
		# we load the hard data -> we will have to use a selective process here
		boreholes = ArchPy.inputs.extract_bhs(df=db, list_bhs=l_bhs, ArchTable=self)
		self.add_bh(boreholes)

		# here we pre-process everything
		self.process_bhs()




## Aare Model ##

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


#Aar_model main function
def AareModel(poly_data, spacing, select_files=False, nreal_units=5, nreal_facies=2, nreal_prop=1,
				ws="data", bhs_path="data/all_BH.csv", all_layers="data/Layer_all_free.csv", mnt="data/MNT25.tif", bdrck_path="data/BEM25-2021_crop_Aar.tif"):
    
    # load files
    lay = pd.read_csv(all_layers, error_bad_lines=False, sep=";", low_memory=False)
    bhs = pd.read_csv(bhs_path)
    
    # mock coordinates
    print(poly_data)
    poly_data = np.load("data/polygon_coord_6.npy") 
    print(poly_data)

    # create multipolygon shapely
    p1 = MultiPolygon([Polygon(p) for p in poly_data])

    # Extract bhs points
    bhs_points = []
    for i, (px, py) in enumerate(zip(bhs.BH_X_LV95, bhs.BH_Y_LV95)):
        po = shapely.geometry.Point(px, py)
        po.name = i  # set cell id as names to grid cells
        bhs_points.append(po)

    #check position, only keep points inside polygon
    l = np.array([po.name for po in bhs_points if po.intersects(p1)])

    #select bhs in zone
    bhs_sel = bhs.loc[l]
    
    #select layers in zone
    lay_sel = lay[lay["BH_GEOQUAT_ID"].isin(bhs_sel["BH_GEOQUAT_ID"])] # layers selection

    #grid 
    sx, sy, sz = spacing
    oz=450
    z1=560
    
    xg = np.arange(p1.bounds[0],p1.bounds[2]+sx,sx)
    nx = len(xg)-1
    yg = np.arange(p1.bounds[1],p1.bounds[3]+sy,sy)
    ny = len(yg)-1
    zg = np.arange(oz,z1+sz,sz)
    nz = len(zg)-1

    dimensions = (nx, ny, nz)
    #spacing = (sx, sy, sz)
    origin = (p1.bounds[0], p1.bounds[1], oz)
    
    # load pile from existing pile (why does he load this from the working directory??)
    # we should change this to be the same directory as we have for the realizations
    T1 = ArchPy.inputs.import_project("Aar_geomodel", ws=ws, 
                                      import_bhs=False, import_grid=False, import_results=False)

    list_facies = T1.get_all_facies()
    T1.rem_all_facies_from_units()
    T1.add_grid(dimensions, spacing, origin, polygon=p1) #, top=mnt, bot=bdrck_path)

    # import geological database 
    db, list_bhs = load_bh_files(bhs_sel, lay_sel.reset_index(), lay_sel.reset_index(),
                                  lbhs_bh_id_col="BH_GEOQUAT_ID", u_bh_id_col="BH_GEOQUAT_ID", fa_bh_id_col="BH_GEOQUAT_ID",
                                  u_top_col = "LA_TOP_m",u_bot_col = "LA_BOT_m",u_ID = "LA_Lithostrati",
                                  fa_top_col = "LA_TOP_m",fa_bot_col = "LA_BOT_m",fa_ID = "LA_USCS_IP_1",
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
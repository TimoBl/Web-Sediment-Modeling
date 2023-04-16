import numpy as np
import matplotlib.pyplot as plt
import geone
import geone.covModel as gcm
import os
import sys
#import pyvista as pv
import ArchPy
import pandas as pd


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


# much more efficient instead of creating a class which has as an attribute an Arch_table
# we can instead define a child as a table
class GeoModel(ArchPy.base.Arch_table):
	def __init__(self, name, dimensions, spacing):
		super().__init__(name=name, working_directory="working_dir", seed=100, verbose=1)

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


'''
# each session has it's own model  
class GeoModel:
	def __init__(self):
		# we first create our arch table
		self.arch_table = ArchPy.base.Arch_table(name="Project", working_directory="working_dir", seed=100, verbose=1) # we will have to see if we can use working_dir, we will have to check if we dockerize this

		# define our simulation grid (this would be our parameters we use)
		dimensions = (50, 50, 50) # number of cells
		spacing = (1, 1, 0.1) # cell dimension
		origin = (0, 0, 0) # origin of the simulation
		self.arch_table.add_grid(dimensions, spacing, origin)

		self.define_model()
		self.pre_process()


	def define_model(self):
		# 1. defining a stratigraphic pile
		P1 = ArchPy.base.Pile("Pile_1")
		self.arch_table.set_Pile_master(P1)

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
		self.arch_table.add_prop(K)


	def pre_process(self):
		# we load the hard data -> we will have to use a selective process here
		boreholes = ArchPy.inputs.extract_bhs(df=db, list_bhs=l_bhs, ArchTable=self.arch_table)
		self.arch_table.add_bh(boreholes)

		# here we pre-process everything
		self.arch_table.process_bhs()
'''
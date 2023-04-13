import numpy as np
import matplotlib.pyplot as plt
import geone
import geone.covModel as gcm
import os
import sys
import pyvista as pv
import ArchPy

# each session has it's own model  
class GeoModel:
	def __init__(self):
		# we first create our arch table
		self.arch_table = ArchPy.base.Arch_table(name="Project", working_directory="working_dir", seed=100, verbose=1) # we will have to see if we can use working_dir, we will have to check if we dockerize this

		# define our simulation grid (this would be our parameters we use)
		self.dimensions = (50, 50, 50) # number of cells
		self.spacing = (1, 1, 0.1) # cell dimension
		self.origin = (0, 0, 0) # origin of the simulation
		self.arch_table.add_grid(dimensions, spacing, origin)

		# 1. defining a stratigraphic pile
		P1 = ArchPy.base.Pile("Pile_1")
		self.arch_table.set_Pile_master(P1)
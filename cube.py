#!/usr/bin/python
# Filename: cube.py

import numpy as np
import iris
import iris.coord_categorisation

def months2seasons(cube):
	"""
	Create seasons from monthly data
	
	"""
	### Create seasonal means (unique and specified 3-month seasons)
	seasons=['mam', 'jja', 'son', 'djf']
	iris.coord_categorisation.add_season(cube, 'time', name='clim_season', seasons=seasons)
	iris.coord_categorisation.add_season_year(cube, 'time', name='season_year', seasons=seasons)
	seasons = cube.aggregated_by(['clim_season', 'season_year'], iris.analysis.MEAN)

	### Remove all of the resultant times which do not cover a three month period.
	### Check bounds and units (e.g., seasons[4].coord('time') ) 
	### before you specify your lambda function
	with iris.FUTURE.context(cell_datetime_objects=False):
		spans_three_months = lambda t: (t.bound[1] - t.bound[0]) > 3 * 28.
		three_months_bound = iris.Constraint(time=spans_three_months)
		complete_seasons = seasons.extract(three_months_bound)

	return complete_seasons



def months2annual(cube):
	"""
	Create annual data from monthly data
	
	"""
	### Create annual means
	iris.coord_categorisation.add_year(cube, 'time', name='year')
	annual = cube.aggregated_by(['year'], iris.analysis.MEAN)

	### Remove all of the resultant times which do not cover a 12 month period.
	### Check bounds and units (e.g., annual[4].coord('time') ) 
	### before you specify your lambda function
	with iris.FUTURE.context(cell_datetime_objects=False):
		spans_twelve_months = lambda t: (t.bound[1] - t.bound[0]) > 12 * 29.
		twelve_months_bound = iris.Constraint(time=spans_twelve_months)
		complete_annual = annual.extract(twelve_months_bound)

	return complete_annual




def unify_dim_coords(cubelist, cube_template, dimensions):
	"""
	If cube[i].dim_coords[n] != cube[j].dim_coords[n] but you know that 
	they are on the same grid then place all cubes on an identical 
	grid (matching cube[0])
	
	Usage:
		unify_dim_coords(cubelist, cube_template, dimensions)
		
	Example:
		unify_dim_coords(my_cubes, my_cubes[0], [1,2])
		
	"""
	for j in dimensions:
		edits = 0
		A =  cube_template.dim_coords[j]
		for i in range(1,len(cubelist)):
			B =  cubelist[i].dim_coords[j]
			if ((A != B) & (A.points.shape == B.points.shape)):
				if (np.max(np.abs(A.points - B.points)) < 0.001):
					edits = edits + 1
					cubelist[i].dim_coords[j].points = cubelist[0].dim_coords[j].points
					cubelist[i].dim_coords[j].bounds = cubelist[0].dim_coords[j].bounds
		if (edits > 0): print "unify_dim_coords: "+str(edits)+" edits to dim_coords["+str(j)+"]"
	return cubelist

# End of cube.py

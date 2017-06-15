import iris

### To do, refactor so that we can also return coords for plot extents etc

def mid_latitudes(cube):
	### to leave off the poles from plots
	cube = cube.intersection( latitude=(-60, 78) )
	return cube

def europe(cube):
	cube = cube.intersection( longitude=(-11.25, 33.75), latitude=(35.1, 72.5) ) ## changed this to look like Fig 3 and 5
	return cube

def nh(cube):
	cube = cube.intersection( latitude=(0, 90) )
	return cube

def sh(cube):
	cube = cube.intersection( latitude=(-90, 0) )
	return cube

def arctic_circle(cube):
	cube = cube.intersection( latitude=(66, 90) )
	return cube

def antarctic_60_90S(cube):
	cube = cube.intersection( latitude=(-90, -60) )
	return cube

def himalayas(cube):
	cube = cube.intersection( longitude=(60, 100), latitude=(15, 45) )
	return cube

def uk(cube):
	cube = cube.intersection( longitude=(-11, 2), latitude=(48, 60) )
	return cube

def france(cube):
	cube = cube.intersection( longitude=(-5, 9), latitude=(41, 52) )
	return cube

def spain(cube):
	cube = cube.intersection( longitude=(-11, 6), latitude=(35, 45) )
	return cube

def egypt(cube):
	cube = cube.intersection( longitude=(22, 39), latitude=(20, 34) )
	return cube
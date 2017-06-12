import matplotlib.pyplot as plt
import iris.quickplot as qplt
import iris.plot as iplt
import iris
import cartopy



def _plot_cubes(plot_type, cube, **kwargs):

	cube = iris.util.squeeze(cube)
	im   = iplt.contourf(cube)

	### Add features
	if kwargs['draw_features'] == True:

		### Find add_feature attribute
		try:
			add_feature = im.ax.add_feature
		except AttributeError:
			pass

		try:
			add_feature = im.axes.add_feature
		except AttributeError:
			pass

		add_feature( cartopy.feature.BORDERS,   linestyle='--' )
		add_feature( cartopy.feature.RIVERS,    color='k'      )
		add_feature( cartopy.feature.COASTLINE, linewidth=2.   )
	
	else:
	
		plt.gca().coastlines()

	### Save image? 
	if (kwargs['fname'] != None): plt.savefig(fname, dpi=dpi)







def contourf(cube, draw_features=False, label=None, fname=None, dpi=150, **kwargs):

	'''
	import matplotlib.pyplot as plt
	import baspy.plot as bplt
	bplt.contourf(cube)
	plt.show()

	* label: Panel labelling (default is None)
		label='a' 
		label=['DJF','MAM', 'JJA', 'SON'] for a cubelist
		label=True for labelling panels sequentially from a to z

	'''

	_plot_cubes( 'contourf', cube, 	
					draw_features=draw_features, label=label, 
					fname=fname, dpi=dpi,
					**kwargs )


def pcolormesh(cube, draw_features=False, label=None, fname=None, dpi=150, **kwargs): 
	_plot_cubes( 'pcolormesh', cube, 
					draw_features=draw_features, label=label, 
					fname=fname, dpi=dpi,
					**kwargs )
	

### To test code above
cube = iris.load_cube(iris.sample_data_path('air_temp.pp'))
cube = contourf(cube, draw_features=True)
plt.show()
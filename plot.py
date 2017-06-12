import matplotlib.pyplot as plt
import iris.quickplot as qplt
import iris.plot as iplt
import iris
import cartopy



def _plot_cubes(plot_type, cube, **kwargs):

	cube = iris.util.squeeze(cube)
	im   = iplt.contourf(cube)

	user_args = kwargs.copy()

	### Add features
	if user_args['draw_features'] == True:

		if (plot_type == 'contourf'):
			im.ax.add_feature( cartopy.feature.BORDERS,   linestyle='--' )
			im.ax.add_feature( cartopy.feature.RIVERS,    color='k'      )
			im.ax.add_feature( cartopy.feature.COASTLINE, linewidth=2.   )
		if (plot_type == 'pcolormesh'):
			im.axes.add_feature( cartopy.feature.BORDERS,   linestyle='--' )
			im.axes.add_feature( cartopy.feature.RIVERS,    color='k'      )
			im.axes.add_feature( cartopy.feature.COASTLINE, linewidth=2.   )

	else:
		plt.gca().coastlines()


	### Save image? 
	if (user_args['fname'] != None): plt.savefig(fname, dpi=dpi)





def contourf(cube, **kwargs):

	'''
	import matplotlib.pyplot as plt
	import baspy.plot as bplt
	bplt.contourf(cube)
	plt.show()

	* label: Panel labelling (default is None)
		e.g., 		label='a' 
				OR	label=['DJF','MAM', 'JJA', 'SON'] for a cubelist
				OR	label=True for labelling panels sequentially from a to z

	'''

	_plot_cubes(contourf, cube, draw_features=False, label=None, fname=None, dpi=150)



def pcolormesh(cube, **kwargs): 
	_plot_cubes(pcolormesh, cube)
	


# cube = iris.load_cube(iris.sample_data_path('air_temp.pp'))
# cube = contourf(cube, draw_features=True)
# plt.show()
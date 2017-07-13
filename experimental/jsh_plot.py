import matplotlib.pyplot as plt
import iris.plot as iplt
import iris
import cartopy
import numpy as np
from matplotlib.offsetbox import AnchoredText

def auto_define_subplot_layout(npanels):
	'''
	ncols, nrows = auto_define_subplot_layout(7)
	'''

	ncols, nrows = 1, 1

	while npanels > (ncols * nrows):
		if (ncols == nrows):  
			ncols = ncols + 1
		else:
			nrows = nrows+1

	return ncols, nrows


def _plot_cubes(plot_type, cubes, fig_num=1, **kwargs):

	### set interactive window
	plt.figure(num=fig_num)

	### set figure title
	if kwargs['suptitle'] != None: plt.suptitle(kwargs['suptitle'])

	### convert cube to cubelist
	if type(cubes) == iris.cube.Cube: cubes = iris.cube.CubeList([cubes])
	if type(cubes) == list: cubes = iris.cube.CubeList(cubes)

	shared_levels = False
	var_names = [cube.var_name for cube in cubes]
	if all([var_names == var_names[0]]): shared_levels = True
	shared_levels = kwargs['shared_levels']

	if shared_levels == True:
		min_val_shared = np.min( [np.min(cube.data) for cube in cubes] )
		max_val_shared = np.max( [np.max(cube.data) for cube in cubes] )

	if type(shared_levels) == list: 
		[min_val_shared, max_val_shared] = shared_levels

	### Decide on the subplot grid layout
	ncubes = len(cubes)
	if (ncubes >= 30): raise ValueError('Soft limit: too many cubes to plot at once')
	ncols, nrows = auto_define_subplot_layout(ncubes)

	### labels
	labels = kwargs['labels']
	if labels == True: labels = list('abcdefghijklmnopqrstuvwxyz')

	### Loop through the cubes, plotting one subplot at a time
	for i, c in enumerate(cubes):

		plt.subplot(nrows, ncols, i+1)

		### ensure these are 2D cubes (if they can be)
		c  = iris.util.squeeze(c)

		### Plot contours
		if shared_levels == False:
			min_val, max_val = np.min(c.data), np.max(c.data)
		else:
			min_val, max_val = min_val_shared, max_val_shared

		cmap='Reds'
		extend_cbar = 'neither'
		if 'Difference' in c.attributes.keys():
			if c.attributes['Difference'] == True:
				cmap='RdBu_r'
				max_val = np.max([ np.abs(np.min(c.data)), np.abs(np.max(c.data)) ])
				min_val = max_val * -1.

		### Overwrite cbar min/max within user data
		if 'cbar_range' in c.attributes.keys(): 
			[min_val, max_val] = c.attributes['cbar_range']
			extend_cbar = 'both'

		levels = np.linspace(min_val, max_val, 11)

		im = iplt.contourf(c, levels, cmap=cmap, extend=extend_cbar)

		### Add features (coastlines, rivers and borders)
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

			add_feature( cartopy.feature.BORDERS,   linestyle='--', alpha=0.4 )
			add_feature( cartopy.feature.RIVERS,    color='k'      )
			add_feature( cartopy.feature.COASTLINE, linewidth=0.7   )
		
		else:
			plt.gca().coastlines()
			

		cbar = plt.colorbar(im, orientation='horizontal')
		cbar.set_label(c.units, size='small')
		cbar.ax.tick_params(labelsize=8)
		plt.title(c.long_name, size='small')

		if (labels != False):
			# Add panel label
			# 'upper right'  : 1,
			# 'upper left'   : 2,
			# 'lower left'   : 3,
			# 'lower right'  : 4,
			plt.gca().add_artist(AnchoredText(labels[i], loc=2, borderpad=0.0, prop=dict(size=8.5) )) ### not working???

	### Save image? 
	fname = kwargs['fname'] 
	dpi   = kwargs['dpi']
	if (fname != None): plt.savefig(fname, dpi=dpi)







def contourf(cubes, draw_features=False, labels=False, 
				fname=None, dpi=150, 
				shared_levels=False, 
				fig_num=1, suptitle=None, **kwargs):

	'''
	import matplotlib.pyplot as plt
	import baspy.plot as bplt
	bplt.contourf(cube)
	plt.show()

	* labels: Panel labelling (default is None)
		labels='a' 
		labels=['DJF','MAM', 'JJA', 'SON'] for a cubelist
		labels=True for labelling panels sequentially from a to z

	You can specify some aspects of the subplot of a cube as follows:
		cube.attributes.update({ 'Difference': True, 'cbar_range': [-1.,1.] })

	shared_levels=[0,7]
	shared_levels=True

	'''

	_plot_cubes( 'contourf', cubes, 	
					draw_features=draw_features, labels=labels, 
					fname=fname, dpi=dpi, shared_levels=shared_levels, 
					fig_num=fig_num, suptitle=suptitle,
					**kwargs )

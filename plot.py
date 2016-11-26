import matplotlib.pyplot as plt
import iris.quickplot as qplt
import iris.plot as iplt
import iris
import cartopy

def cplt(cube, fname=None, dpi=150, draw_features=False):
	
	'''
	clever plotting :-)
	'''

	### Quick Plot
	if (fname==None):	 
		save_plot = False
		im = qplt.contourf(cube)
		if (draw_features == False): plt.gca().coastlines()

	### Iris Plot (more detailed)
	if (fname!=None):
		save_plot = True
		im = iplt.contourf(cube)

	### Add features
	if draw_features == True:
		im.ax.add_feature(cartopy.feature.BORDERS,   linestyle='--')
		im.ax.add_feature(cartopy.feature.RIVERS,    color='k')
		im.ax.add_feature(cartopy.feature.COASTLINE, linewidth=2.)

	### Save image? 
	if save_plot == True: 
		plt.savefig(fname, dpi=dpi)
	else:
		iplt.show()



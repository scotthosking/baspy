import matplotlib.pyplot as plt
import iris.plot as iplt
import iris
import cartopy
import cartopy.feature as cfe
import cartopy.crs as ccrs
import numpy as np
from matplotlib.offsetbox import AnchoredText

'''
To do:
    * Specifiy nrow & ncol labels
    * shifted (non-centred) colour-scale
    * Add markers at lat/lon locations
'''


def _add_source(name):
    ### bottom left corner of figure
    plt.annotate(name, xy=(0.01,0.01), xycoords='figure fraction', 
                    color='Grey', ha='left', size='small')


def _add_author(name=None):
    ### bottom right corner of figure
    if name == None:
        import pwd, os
        name = pwd.getpwuid(os.getuid())[4]
    plt.annotate(name, xy=(0.99,0.01), xycoords='figure fraction', 
                    color='Grey', ha='right', size='small')


def auto_define_subplot_layout(npanels, fix_ncols=False, fix_nrows=False):
    '''
    ncols, nrows = auto_define_subplot_layout(7)
    '''

    ### Initialise values (update below)
    ncols, nrows = 1, 1

    ### If ncols AND nrows ARE specified by user
    if (fix_ncols != False) & (fix_nrows != False):
        return fix_ncols, fix_nrows

    ### If ncols AND nrows ARE NOT specified by user
    if (fix_ncols == False) & (fix_nrows == False):
        while npanels > (ncols * nrows):
            if (ncols == nrows):  
                ncols = ncols + 1
            else:
                nrows = nrows+1
        return ncols, nrows

    ### If only ncols is specified by user
    if (fix_ncols != False) & (fix_nrows == False):
        while npanels > (fix_ncols * nrows):
            nrows = nrows+1
        return fix_ncols, nrows

    ### If only nrows specified by user
    if (fix_ncols == False) & (fix_nrows != False):
        while npanels > (ncols * fix_nrows):
            ncols = ncols + 1
        return ncols, fix_nrows

    ### Should not get this far
    raise ValueError('Something has gone wrong in defining the subplot layout')


def draw_regional_box( region, transform=None ):
    '''
    Draw box around a region on a map

    region = [west,east,south,north]
    '''

    west, east, south, north = region

    if transform == None:
        transform = ccrs.PlateCarree()

    plt.plot([west, west], [south,north], 'k-', transform=transform, linewidth=0.7)
    plt.plot([east,east], [south,north], 'k-', transform=transform, linewidth=0.7)
    for i in range( np.int(west),np.int(east) ): 
        plt.plot([i,i+1], [south,south], 'k-', transform=transform, linewidth=0.7)
        plt.plot([i,i+1], [north,north], 'k-', transform=transform, linewidth=0.7)


def plot_markers(lons, lats, marker='o', transform=None):
    
    if (type(lons) == int) | (type(lons) == float): lons = np.array([lons])
    if (type(lats) == int) | (type(lats) == float): lats = np.array([lats])

    if len(lons) != len(lats):
        raise ValueError('lons and lats are different lengths')

    if transform == None:
        transform = ccrs.PlateCarree()

    for lon, lat in zip(lons, lats):
        plt.plot(lon, lat, marker, color='k', ms=7, mec='w', mew=2., mfc='none', transform=transform)
        plt.plot(lon, lat, marker, color='k', ms=7, mfc='none', transform=transform)


'''
Main definition
'''

def maps(cubes, plot_type='contourf', 
            fname=None, dpi=150, figsize=None, fig_num=1, tight_layout=False,
            fix_ncols=False, fix_nrows=False, 
            shared_levels=False, hide_colbars=False, shared_colbar=False, shared_cbar_label=None,
            show_coastlines=True, show_rivers=False, show_borders=False, show_ocean=None, show_iceshelves=False, 
            region_mask=None,
            suptitle=None, show_titles=True, labels=False, add_author=False, add_source=False,
            draw_box=False, add_markers=None, marker_style='o',
            map_projection=None, set_extent=None):

    '''
    import matplotlib.pyplot as plt
    from baspy.experimental import jsh_plot as bplt
    bplt.plot_maps(cube)
    plt.show()

    * labels: Panel labelling (default is None)
        labels='a' 
        labels=['DJF','MAM', 'JJA', 'SON'] for a cubelist
        labels=True for labelling panels sequentially from a to z

    You can specify some aspects of the subplot of a cube as follows:
        cube.attributes.update({ 'Difference': True, 'cbar_range': [-1.,1.] })

    Force all panels to use shared contour levels unless specified otherwise in cube.attributes
        shared_levels=[0,7]
        shared_levels=True

    '''

    ### convert cube or list of cubes to a cubelist
    if type(cubes) == iris.cube.Cube: cubes = iris.cube.CubeList([cubes])
    if type(cubes) == list: cubes = iris.cube.CubeList(cubes)

    ### Shared Contour levels (use unless specified within cube.attributes)
    if shared_levels == True:
        min_val_shared = np.min( [np.min(cube.data) for cube in cubes] )
        max_val_shared = np.max( [np.max(cube.data) for cube in cubes] )

    if type(shared_levels) == list: 
        [min_val_shared, max_val_shared] = shared_levels

    ### Decide on the subplot grid layout
    ncubes = len(cubes)
    if (ncubes > 60): raise ValueError('Soft limit reached: too many cubes to plot at once')
    ncols, nrows = auto_define_subplot_layout(ncubes, fix_ncols=fix_ncols, fix_nrows=fix_nrows)

    ### From the grid layout, decide on figure size (width, height)
    if figsize == None:
        ### Fix height as VDUs are usually widescreen
        ### width can fit with height limitations
        
        fig_ratio  = float(nrows) / float(ncols)

        fig_height = nrows * 4.2
        fig_width  = round( (fig_height / fig_ratio), 1) # 1 decimal place

        if fig_width > 12.:
            ### Too wide!! constrain width and re-adjust height (keeping same ratio)
            fig_width  = 12.
            fig_height = round( (fig_ratio * fig_width), 1)

        if fig_height > 12.:
            ### Too high!! constrain height and re-adjust width (keeping same ratio)
            fig_height  = 12.
            fig_width = round( (fig_height / fig_ratio), 1)



        figsize = (fig_width,fig_height)
        print('Setting: figsize=',figsize)

    ### Setting up figure
    plt.close(fig_num) # close if existing fig_num exists 
    fig = plt.figure( figsize=figsize, num=fig_num )

    ### set figure title
    if suptitle != None: plt.suptitle(suptitle)

    ### labelling
    if labels == True: labels = list('abcdefghijklmnopqrstuvwxyz')



    ##################################
    ### Loop through the cubes, 
    ### plotting one subplot at a time
    ##################################
    for i, c in enumerate(cubes):

        ax = plt.subplot(nrows, ncols, i+1, projection=map_projection)

        if set_extent != None:
            ax.set_extent(set_extent, ccrs.PlateCarree())

        ### ensure these are 2D cubes (if they can be)
        c  = iris.util.squeeze(c)

        ### Plot contour levels and cmap setup
        if shared_levels == False:
            min_val, max_val = np.min(c.data), np.max(c.data)
        else:
            min_val, max_val = min_val_shared, max_val_shared

        ### Standard plot (default values)
        cmap = 'Reds'
        extend_cbar = 'neither'

        ### Region mask
        if region_mask != None:
            from baspy.util import region_mask as _region_mask
            c = _region_mask(c, region_mask) ### is it better to run this once for all cubes???
            if (show_ocean == None): show_ocean = True
            

        ### Difference plot
        if 'Difference' in c.attributes.keys():
            if c.attributes['Difference'] == True:
                max_val = np.max([ np.abs(np.min(c.data)), np.abs(np.max(c.data)) ])
                min_val = max_val * -1.

        if np.abs(min_val) == np.abs(max_val):
            cmap='RdBu_r'
            extend_cbar = 'both'

        ### Overwrite cbar min/max within user data
        if 'cbar_range' in c.attributes.keys(): 
            [min_val, max_val] = c.attributes['cbar_range']
            extend_cbar = 'both'

        if 'cbar_extend' in c.attributes.keys(): 
            extend_cbar = c.attributes['cbar_extend']

        levels = np.linspace(min_val, max_val, 11)

        ### plot data
        if plot_type == 'contourf':
            im = iplt.contourf(c, levels, cmap=cmap, extend=extend_cbar)
        if plot_type == 'pcolormesh':
            im = iplt.pcolormesh(c, levels, cmap=cmap, extend=extend_cbar)


        ### Add features (coastlines, rivers and borders)
        if plot_type == 'contourf':   add_feature = im.ax.add_feature
        if plot_type == 'pcolormesh': add_feature = im.axes.add_feature

        if show_rivers == True:
            add_feature( cartopy.feature.RIVERS )
        if show_borders == True:
            add_feature( cartopy.feature.BORDERS, linestyle='-', alpha=0.4 )
        if (show_coastlines == True) & (show_iceshelves == False):
            add_feature( cartopy.feature.COASTLINE, linewidth=0.7 ) # plt.gca().coastlines()
        if show_ocean == True:
            add_feature( cartopy.feature.OCEAN, edgecolor='k', facecolor='LightGrey' )
        if show_iceshelves == True:
            add_feature(cfe.NaturalEarthFeature('physical', 'antarctic_ice_shelves_polys', '50m',
                                                            edgecolor='k', facecolor='none', linewidth=0.2 ) )
            add_feature(cfe.NaturalEarthFeature('physical', 'coastline', '50m', 
                                                            edgecolor='k', facecolor='none', linewidth=0.4) )
            add_feature(cfe.NaturalEarthFeature('physical', 'antarctic_ice_shelves_lines', '50m',
                                                            edgecolor='k', facecolor='none', linewidth=0.4 ) )




        ### colour bar
        hide_colbar = hide_colbars
        if 'hide_colbar' in c.attributes.keys():
            hide_colbar = c.attributes['hide_colbar']

        units_label = c.units
        if units_label == 'degreesC': units_label = r'$\degree$C'

        if 'units_label' in c.attributes.keys():
            units_label = c.attributes['units_label']

        if (hide_colbar == False) | (shared_colbar == False):
            cbar = plt.colorbar(im, orientation='horizontal')
            cbar.set_label(units_label, size='small')
            cbar.ax.tick_params(labelsize=8)
        
        ### Panel Title
        if show_titles == True:
            panel_title = c.long_name
        else:
            panel_title = None

        if 'Title' in c.attributes.keys():
            panel_title = c.attributes['Title']
        
        if panel_title != None:    
            plt.title(panel_title, size='small')

        ### Panel Labelling
        if (labels != False):
            # 1='upper right', 2='upper left' 3='lower left', 4='lower right'
            plt.gca().add_artist(AnchoredText(labels[i], loc=2, borderpad=0.0, 
                                    prop=dict(size=8.5) ))

        ### Draw box around region
        if draw_box != False:
            if len(draw_box) == 4:
                draw_regional_box(draw_box)
            else:
                raise ValueError()

        ### Add markers
        if add_markers != None:
        	lons, lats = add_markers  
	        plot_markers(lons, lats, marker=marker_style)

        ### Colour bar positioning for shared colourbar (shared_colbar)
        left_tmp, bottom, width, height = plt.gca().get_position().bounds
        if i == 0: left_positions = np.array([])
        left_positions = np.append(left_positions,left_tmp)

    ### Shared colorbar
    if shared_colbar == True: ### TO DO: only add when all plots have matching units + levels !!!!
        width = np.max(left_positions) - np.min(left_positions) + width
        colorbar_axes = fig.add_axes([np.min(left_positions), bottom/1.5, width, 0.025])   
        cbar = plt.colorbar(im, colorbar_axes, orientation='horizontal', format='%2.1f')
        cbar.ax.tick_params(labelsize=8) 
        cbar.set_label(shared_cbar_label)

    ### Add text on Figure
    if add_author == True: _add_author()
    if type(add_author) == str: _add_author(add_author)
    if type(add_source) == str: _add_source(add_source)

    ### Tight layout (reduce white-space) - can cause problems
    if tight_layout == True: plt.tight_layout()

    ### Save image
    if (fname != None): plt.savefig(fname, dpi=dpi)

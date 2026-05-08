import baspy as bp
from baspy._iris import downscaling as SD
import iris


def edit_erai_attrs(cube, field, filename):
    ### Remove attributes from cube on read
    cube.attributes.pop('history', None)
    cube.attributes.pop('time',    None)
    cube.attributes.pop('date',    None)
    cube.attributes.pop('valid_max',    None)
    cube.attributes.pop('valid_min',    None)
    # cube.coord('t').attributes.pop('time_origin', None)

    ### Add additional time coordinate categorisations
    if (len(cube.coords(axis='t')) > 0):
        time_name = cube.coord(axis='t').var_name
        iris.coord_categorisation.add_year(cube, time_name, name='year')
        iris.coord_categorisation.add_month_number(cube, time_name, name='month')
        iris.coord_categorisation.add_day_of_year(cube, time_name, name='day_of_year')
        seasons = ['djf', 'mam', 'jja', 'son']
        iris.coord_categorisation.add_season(cube, time_name, name='clim_season', seasons=seasons)
        iris.coord_categorisation.add_season_year(cube, time_name, name='season_year', seasons=seasons)

region_bounds = bp.region.Sub_regions.central_england 



### Historical period

hist_con = iris.Constraint(year=lambda y: 1979 <= y <= 2004)

erai = iris.load_cube('/group_workspaces/jasmin4/bas_climate/data/ecmwf/era-interim/mon/surface/t2m_mon.nc',
                        callback=edit_erai_attrs, constraint=hist_con)
erai = bp.region.extract(erai, region_bounds)

hist_catlg = bp.catalogue(Experiment='historical', Frequency='mon', Model='HadGEM2-CC', Var='tas', RunID='r1i1p1')
hist = bp.get_cube(hist_catlg, constraints=hist_con)
hist = bp.region.extract(hist, region_bounds)


### Future Period
fut_con = iris.Constraint(year=lambda y: 2070 <= y <= 2100)
fut_catlg = bp.catalogue(Experiment='rcp45', Frequency='mon', Model='HadGEM2-CC', Var='tas', RunID='r1i1p1')
fut = bp.get_cube(fut_catlg, constraints=fut_con)
fut = bp.region.extract(fut, region_bounds)

print(erai.summary)
print(hist.summary)
print(fut.summary)

sh,bc    = SD.bias_correction(erai, hist, fut)
delta,cf = SD.change_factor(erai, hist, fut)

qmbc = SD.qm_bias_correction(erai, hist, fut)
qmcf = SD.qm_change_factor(erai, hist, fut)
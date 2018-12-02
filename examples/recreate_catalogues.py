import baspy as bp

cmip5_cat = bp.catalogue(dataset='cmip5', refresh=True)
happi_cat = bp.catalogue(dataset='happi', refresh=True)

print('done')

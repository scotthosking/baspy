import esmcat as ecat

cmip5_cat = ecat.catalogue(dataset='cmip5', refresh=True)
happi_cat = ecat.catalogue(dataset='happi', refresh=True)
cmip6_cat = ecat.catalogue(dataset='cmip6', refresh=True)

print('done')

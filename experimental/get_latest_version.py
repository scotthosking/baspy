import numpy as np
from baspy import cat2
import baspy as bp

### use experimental catalogue - which ensures a complete set of variables as standard
catlg = cat2.catalogue(dataset='cmip5_all_versions', Var=['tas','pr'], Frequency='day')

catlg = catlg[catlg['Version'] != 'latest'] # why do these Version ids exist?? !!

if 'cmip5' not in catlg['dataset'].iloc[0]:
    raise ValueError('currently this only works for CMIP5 cataloging')


### convert Version strings into integers (e.g., 'v20110101' --> 20110101)
catlg['Version'] = catlg['Version'].map(lambda x: x.lstrip('v')).astype(int)


### add column of Version numbers we can tweak and sort
catlg['VersionToSort'] = catlg['Version']


### tweak version numbers ready to sort
catlg.loc[ (catlg['Model'] == 'ACCESS1-0') & (catlg['Version'] < 2000_00_00), 'VersionToSort' ] += 1_000_000_000
## add more models !!!



### Get rows with max Version ID where all vars present (use observed=True as we have 'category' columns)
latest_versions = catlg.groupby(['Model', 'Experiment', 'RunID'], observed=True).max()['VersionToSort'].reset_index() 

latest_versions['VersionToSort']            = latest_versions['VersionToSort'].astype(str)
latest_versions['Unique_Model_Run_Version'] = latest_versions[['Model', 'Experiment', 'RunID', 'VersionToSort']].apply(lambda x: '_'.join(x), axis=1)
catlg['VersionToSort']                      = catlg['VersionToSort'].astype(str)
catlg['Unique_Model_Run_Version']           = catlg[['Model', 'Experiment', 'RunID', 'VersionToSort']].apply(lambda x: '_'.join(x), axis=1)

catlg = catlg[  catlg['Unique_Model_Run_Version'].isin(latest_versions['Unique_Model_Run_Version']) ]


### Clean-up
catlg = catlg.drop( labels=['Unique_Model_Run_Version','VersionToSort'], axis=1 )
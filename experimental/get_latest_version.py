import baspy as bp
import numpy as np


def get_newest_version(catlg):

    if dataset != 'cmip5':
        raise ValueError('currently this only works for CMIP5 cataloging')

    ### add column of Version numbers we can sort (Check with Tony!!!)
    ### may need to do this model-by-model ?
    catlg['VersionToSort'] = catlg['Version'].replace({'v1':'v01',
                                                       'v2':'v02',
                                                       'v3':'v03',
                                                       'v4':'v04'})

    ### Get rows with max Version ID where all vars present
    latest_versions = catlg.groupby('Unique_Model_Run').max()['VersionToSort'].reset_index()

    latest_versions['Unique_Model_Run_Version'] = latest_versions['Unique_Model_Run'] + '_' +latest_versions['VersionToSort']
    catlg['Unique_Model_Run_Version']           = catlg['Unique_Model_Run'] + '_' +catlg['Version']

    catlg = catlg[  catlg['Unique_Model_Run_Version'].isin(latest_versions['Unique_Model_Run_Version']) ]


    ### Clean-up
    catlg = catlg.drop( labels=['Unique_Model_Run_Version','VersionToSort'], axis=1 )

    return catlg




catlg = bp.catalogue(dataset='cmip5_all_versions', Var=['tas','pr'], 
                        Experiment=['historical'],
                        Frequency='day', RunID='r1i1p1', 
                        complete_var_set=True) # complete_var_set should always be true when more than 1 var specified


catlg = catlg.drop_duplicates() # these comes from the symbolic links used in the Version folders (e.g., Version --> 20110524)
# ^ do this before we save the catalogue


catlg = get_newest_version(catlg)


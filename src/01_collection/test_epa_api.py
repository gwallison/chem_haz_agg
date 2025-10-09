# Import the specific functions you need from your client script.
import pandas as pd
import os
import epa_api_client as eac
import config

dummy = pd.DataFrame()
column_keep = ['dtxsid','casrn','preferredName',
               'qcLevel','henrysLawAtm']
def make_fresh_chem_dictionary():
    cols = {}
    for col in column_keep:
        cols[col] = []
        
    return cols

def update_epa_chem_df(inchemdf = dummy, onlynew=False):
    """ 
    chemdf has, at minimum, 'DTXSID' column. This search depends
    on that ID.
    
    If no chemlist supplied, update from data/01_raw/comp_tox_casrn_dtxsid_master.csv

    If onlynew=True, just append new data onto existing,
    otherwise update all on chemlist.
    
    """
    if len(inchemdf)==0:
        inchemdf = pd.read_csv(config.COMPTOX_CASRN_DTXSID_MASTER)
    # print(inchemdf.columns)
    # print(inchemdf.head())    
    # print(len(inchemdf))
    outfn = config.EPA_CHEM_MASTER     
    # try:
    #     outdf = pd.read_parquet(outfn)
    #     workdic = outdf.to_dict()
    # except:
    #     print('Creating new output data frame for "update_epa_chem"')
    workdic = make_fresh_chem_dictionary()
    
    for dtxsid in inchemdf[inchemdf.DTXSID.notna()].DTXSID.tolist():
        try:
            response = eac.get_chemical_details(dtxsid)
            for var in column_keep:
                workdic[var].append(response[var])
                print(f'{var}: {response[var]}')
        except:
            print(f'\nBad response for DTXSID: {dtxsid}')
    pd.DataFrame(workdic).to_parquet(outfn)
    print(f'\n ****  wrote dataframe to {outfn}')

def main():
    """  """
    inchemdf = pd.DataFrame()
    update_epa_chem_df(inchemdf)
    
if __name__ == "__main__":
    main()



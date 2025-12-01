# Import the specific functions you need from your client script.
import pandas as pd
import time
import epa_api_client as eac
import config
import master_list_manager as mlm

dummy = pd.DataFrame()
column_keep = ['dtxsid','casrn','dtxcid','compoundId','genericSubstanceId',
               'preferredName','qcLevel','henrysLawAtm']
def make_fresh_chem_dictionary():
    cols = {}
    for col in column_keep:
        cols[col] = []
        
    return cols

def update_epa_chem_df():
    """ 
    If no chemlist supplied, update from data/01_raw/comp_tox_casrn_dtxsid_master.csv

    If onlynew=True, just append new data onto existing,
    otherwise update all on chemlist.
    
    """
    mastcasdf = mlm.get_master_df()
    try:
        epadf = pd.read_parquet(config.EPA_CHEM_MASTER)
        print('Got it.')
    except:
        epadf = pd.DataFrame(make_fresh_chem_dictionary())
    
    workdic = make_fresh_chem_dictionary()
    
    allcas = set(mastcasdf.CASRN.unique())
    epacas = set(epadf.casrn.unique())
    workcas = list(allcas.difference(epacas))
    print(len(allcas),len(epacas),len(workcas))
    print(f'Number to analyze: {len(workcas)}')
    
    if len(workcas)==0:
        print('No CAS to be updated')
        return 0
            
    inchemdf = mastcasdf[mastcasdf.CASRN.isin(workcas)].copy()
    print(len(inchemdf))
    
    for dtxsids in inchemdf[inchemdf.DTXSIDs.notna()].DTXSIDs.tolist():
        try:
            for dtxsid in dtxsids:
                response = eac.get_chemical_details(dtxsid)
                # print(response)
                for var in column_keep:
                    workdic[var].append(response[var])
                    print(f'{var}: {response[var]}')
        except:
            print(f'\nBad response for DTXSID: {dtxsid}')
        time.sleep(2)
    print(len(workdic))    
    new = pd.DataFrame(workdic)
    out = pd.concat([epadf,new])
    out.to_parquet(config.EPA_CHEM_MASTER)
    # print(f'\n ****  wrote dataframe to {outfn}')

def main():
    """  """
    update_epa_chem_df()
    
if __name__ == "__main__":
    main()



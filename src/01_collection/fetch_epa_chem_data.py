# Import the specific functions you need from your client script.
import os
import sys
import pandas as pd
import time

# Add the project root to the Python path to resolve the 'config' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import epa_api_client as eac
import config
import master_list_manager as mlm

dummy = pd.DataFrame()
column_keep = ['dtxsid','casrn','dtxcid','compoundId','genericSubstanceId',
               'preferredName','qcLevel','qcNotes',
               'henrysLawAtm','molFormula','multicomponent',
               "totalAssays","toxcastSelect","activeAssays","percentAssays",
               'pubmedCount','pubchemCount','sourcesCount','wikipediaArticle','cpdataCount',
               'hasStructureImage']
def make_fresh_chem_dictionary():
    cols = {}
    for col in column_keep:
        cols[col] = []
        
    return cols

def update_epa_chem_df():
    """ 
    If no chemlist supplied, update from data/01_raw/comp_tox_casrn_dtxsid_master.csv

    If changing code, delete config.EPA_CHEM_MASTER to get fresh copies   
    """
    mastcasdf = mlm.get_master_df()
    try:
        epadf = pd.read_parquet(config.EPA_CHEM_MASTER)
        print('Got it.')
    except:
        epadf = pd.DataFrame(make_fresh_chem_dictionary())
    
    
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
                workdic = make_fresh_chem_dictionary()
                response = eac.get_chemical_details(dtxsid)
                # print(response)
                for var in column_keep:
                    workdic[var].append(response[var])
                    print(f'{var}: {response[var]}')
                new = pd.DataFrame(workdic)
                epadf = pd.concat([epadf,new])
                epadf.to_parquet(config.EPA_CHEM_MASTER)
                
        except Exception as e:
            print(f'\nBad response for DTXSID: {dtxsid}: {e}')
        time.sleep(4)
    print(len(workdic))    
    # print(f'\n ****  wrote dataframe to {outfn}')

def main():
    """ To create fresh set, delete config.EPA_CHEM_MASTER first
    Getting data from EPA will take many hours"""
    update_epa_chem_df()
    
if __name__ == "__main__":
    main()



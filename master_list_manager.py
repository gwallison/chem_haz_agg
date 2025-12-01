import pandas as pd
from pathlib import Path
import datetime
import os
import numpy as np
import config

# Define the path to the master file.

MASTER_FILE_FN = config.MASTER_CAS_LIST
MASTER_COLUMNS = ['CASRN', 'orig_source', 'date_added','DTXSID','ec_numbers']

def get_master_df():
    return pd.read_parquet(MASTER_FILE_FN)

def save_master_df(df):
    """ saves master and a simple csv for COMPTOX purposes"""
    df.to_parquet(MASTER_FILE_FN)
    df.to_csv(config.TEMP_CASRN_CSV)
        

def add_casrns(new_casrns: list[str], source: str) -> int:
    """Adds new CASRNs to the master Parquet file, avoiding duplicates."""
    master_df = get_master_df()

    existing_casrns = set(master_df['CASRN'])
    unique_new_casrns = [cas for cas in new_casrns if cas not in existing_casrns]

    if not unique_new_casrns:
        print("No new records to add. All provided CASRNs already exist.")
        return 0

    new_records_df = pd.DataFrame({
        'CASRN': unique_new_casrns,
        'orig_source': source,
        'date_added': pd.to_datetime(datetime.date.today())

    })

    if master_df.empty:
        updated_df = new_records_df
    else:
        updated_df = pd.concat([master_df, new_records_df], ignore_index=True)

    updated_df.to_parquet(MASTER_FILE_FN, index=False, engine='pyarrow')
    print(f"✅ Successfully added {len(unique_new_casrns)} new records from source '{source}'.")
    return len(unique_new_casrns)

def casrn_exists(casrn: str) -> bool:
    """Checks if a single CASRN exists in the master list."""
    ## possible refactor: don't fetch whole file, use parquet filter for CASRN
    master_df = pd.read_parquet(MASTER_FILE_FN)
    return casrn in master_df['CASRN'].values

def casrns_exist(casrns_to_check: list[str]) -> dict:
    """Checks a list of CASRNs against the master list and sorts them."""
    master_df = pd.read_parquet(MASTER_FILE_FN)
    existing_casrns_set = set(master_df['CASRN'])
    found = [cas for cas in casrns_to_check if cas in existing_casrns_set]
    missing = [cas for cas in casrns_to_check if cas not in existing_casrns_set]
    return {'existing': found, 'missing': missing}

# --- UPDATED GENERIC FUNCTION ---
def add_casrns_from_file(file_path: str | Path, source_name: str, casrn_column: str = 'CASRN') -> int:
    """
    Extracts unique CASRNs from a generic parquet file and adds them.

    Args:
        file_path (str or Path): The path to the data file.
        source_name (str): The name to assign as the source for these CASRNs.
        casrn_column (str, optional): The name of the column containing the CASRNs.
                                      Defaults to 'CASRN'.

    Returns:
        int: The number of new, unique records added to the master list.
    """
    try:
        source_df = pd.read_parquet(file_path)
    except FileNotFoundError:
        print(f"❌ Error: The file was not found at {file_path}")
        return 0

    if casrn_column not in source_df.columns:
        print(f"❌ Error: Column '{casrn_column}' not found in the file at {file_path}.")
        return 0

    unique_casrns = source_df[casrn_column].unique().tolist()
    print(f"Found {len(unique_casrns)} unique CASRNs in column '{casrn_column}' from source '{source_name}'.")

    num_added = add_casrns(new_casrns=unique_casrns, source=source_name)
    return num_added

# --- REFACTORED FracFocus FUNCTION ---
def add_from_FracFocus(file_path: str | Path) -> int:
    """
    Extracts CASRNs from a FracFocus file by calling the generic function.
    
    This is now a simple wrapper around the more flexible 'add_casrns_from_file'.
    """
    return add_casrns_from_file(
        file_path=file_path,
        source_name='FracFocus',
        casrn_column='bgCAS'  # Specify the non-default column name
    )

def print_summary():
    df = get_master_df()
    print('\n'+'='*10, ' MASTER CHEM LIST  Summary ','='*10,'\n')
    print(f'   Number of chemicals: {len(df):5}')
    print(f'            Num DTXSID: {len(df[df.DTXSIDs.notna()]):5}')
    print(f'            Num ec_ids: {len(df[df.ec_numbers.notna()]):5}\n')
    df = df.sort_values('date_added',ascending=False)
    print(f'   Most recent addition: {(df.iloc[0].date_added).date()}')
    print(f'   Most recent source: {(df.iloc[0].orig_source)}')
    print('='*49)
    
def add_from_build_nb():
    """
    This looks to the build_nb new cas file and attempts to add 
    these to the master chem list

    Returns
    -------
    None.

    """
    print('*** New cas to Master Chem List? ***')
    new_cas_in_FF_build = r"C:\MyDocs\integrated\openFF\build\sandbox\work_dir\new_cas_added.parquet"
    add_casrns_from_file(new_cas_in_FF_build,
                         'FracFocus',
                         'CASNumber')
    print_summary()

def update_DTXSID():
    """
    Run this after fetching COMPTOX CASRN:DTXSID file.
    
    uses output of CompTox bulk summary EXCEL file to add
    any new DTXSID numbers to existing.  Looks for most recent xlsx file
    with appropriate prefix to use as source.


    Returns
    -------
    Number of records updated

    """
    def update_row(master_row,DTXSID):
        # import math
        # print(master_row.CASRN, DTXSID)
        if (pd.isna(DTXSID)):
            return master_row.DTXSIDs, False # don't change anything

        if isinstance(master_row.DTXSIDs, np.ndarray):
            wlst = list(master_row.DTXSIDs)
        else:
            print(type(master_row.DTXSIDs))
            wlst = []
            
        if not DTXSID in wlst:
            wlst.append(DTXSID)
            return wlst, True
        return master_row.DTXSIDs, False # keeps the value
            
    dlst = os.listdir(config.RAW_DATA)
    targets = []
    # print(dlst)
    for fn in dlst:
        fnlst = fn.split('_')
        # print(fn[-3:])
        if (fn[-3:] == 'csv') & (fnlst[0]=='CCD-Batch-Search'):
            # print(fn)
            targets.append(fn)

    targets.sort(reverse=True)
    # print(f'targets: {targets}')
    if len(targets)==0:
        print('NO APPROPRIATE *CSV* COMPTOX FILE IN RAW!  NOT UPDATED!')
        return 0
    
    ctdf = pd.read_csv(os.path.join(config.RAW_DATA,targets[0]))
    c = ctdf.DTXSID.notna()
    print(f'Using "{targets[0]}" as DTXSID source')
    total = len(ctdf)
    num = len(ctdf[c])
    print(f'   - CASRN with DTXSID: {num:,};  without: {total-num:,}')
    
    updated = []
    newdtxsid = []
    df = get_master_df()
    for i,row in df.iterrows():
        cas = row.CASRN
        epadtx = ctdf[ctdf.INPUT==cas].DTXSID.tolist()
        if len(epadtx)>1:
            print("MORE THAN ONE DTXSID! Need to change logic to capture!")
        res = update_row(row, epadtx[0])
        newdtxsid.append(res[0])
        if res[1]: updated.append(cas)
        
    df.DTXSIDs = newdtxsid
    
    # print(df.head())
    print(f' Updated: {len(updated)}')
    save_master_df(df)
    
if __name__ == '__main__':

    update_DTXSID()
    # new_in_ECMC = r"C:\Users\Gary\Downloads\ECMC_summary_dashboard (1).csv"
    # tmpdf = pd.read_csv(new_in_ECMC)
    # tmpfn = r"C:\MyDocs\integrated\gwa_local\tmp\ecmc_new_chem.parquet"
    # tmpdf.to_parquet(tmpfn)
    # add_casrns_from_file(tmpfn,
    #                      'ECMC disclosures',
    #                      'CAS Number')
    # print_summary()
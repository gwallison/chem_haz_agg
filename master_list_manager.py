import pandas as pd
from pathlib import Path
import datetime
import os
import config

# Define the path to the master file.
# MASTER_FILE_DIR = r"C:/MyDocs/integrated/chem_profiles/data/03_processed"
# MASTER_FILE_FN = os.path.join(MASTER_FILE_DIR,'master_cas_list.parquet')
# MASTER_FILE_PATH = Path(MASTER_FILE_FN)

MASTER_FILE_FN = config.MASTER_CAS_LIST
MASTER_COLUMNS = ['CASRN', 'orig_source', 'date_added']

def get_master_df():
    return pd.read_parquet(MASTER_FILE_FN)

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


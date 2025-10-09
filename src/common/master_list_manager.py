import pandas as pd
from pathlib import Path
import datetime
import os

# Define the path to the master file.
MASTER_FILE_DIR = r"C:/MyDocs/integrated/chem_profiles/data/03_processed"
MASTER_FILE_FN = os.path.join(MASTER_FILE_DIR,'master_cas_list.parquet')
MASTER_FILE_PATH = Path(MASTER_FILE_FN)
MASTER_COLUMNS = ['CASRN', 'orig_source', 'date_added']

def get_master_df():
    return pd.read_parquet(MASTER_FILE_PATH)

def add_casrns(new_casrns: list[str], source: str) -> int:
    """Adds new CASRNs to the master Parquet file, avoiding duplicates."""
    MASTER_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if MASTER_FILE_PATH.exists():
        master_df = pd.read_parquet(MASTER_FILE_PATH)
    else:
        master_df = pd.DataFrame(columns=MASTER_COLUMNS)
        print("Master file not found. A new one will be created.")

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

    updated_df.to_parquet(MASTER_FILE_PATH, index=False, engine='pyarrow')
    print(f"✅ Successfully added {len(unique_new_casrns)} new records from source '{source}'.")
    return len(unique_new_casrns)

def casrn_exists(casrn: str) -> bool:
    """Checks if a single CASRN exists in the master list."""
    if not MASTER_FILE_PATH.exists():
        return False
    master_df = pd.read_parquet(MASTER_FILE_PATH)
    return casrn in master_df['CASRN'].values

def casrns_exist(casrns_to_check: list[str]) -> dict:
    """Checks a list of CASRNs against the master list and sorts them."""
    if not MASTER_FILE_PATH.exists():
        return {'existing': [], 'missing': casrns_to_check}
    master_df = pd.read_parquet(MASTER_FILE_PATH)
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

# --- Example of how to use ALL functions ---
# if __name__ == '__main__':
#     # 1. Add initial data
#     print("--- Adding initial data ---")
#     add_casrns(new_casrns=['50-00-0', '71-43-2', '108-88-3'], source='Initial_Seed_List')
#     print("-" * 35)

#     # 2. Test FracFocus addition (now uses the refactored function)
#     print("--- Testing FracFocus addition ---")
#     dummy_ff_path = Path('data/dummy_fracfocus.parquet')
#     dummy_ff_data = pd.DataFrame({'bgCAS': ['108-88-3', '75-01-4', '999-99-9']})
#     dummy_ff_data.to_parquet(dummy_ff_path, index=False)
#     print(f"Created dummy FracFocus file at '{dummy_ff_path}'")
#     add_from_FracFocus(dummy_ff_path)
#     print("-" * 35)

#     # 3. Test generic file addition (using the default 'CASRN' column)
#     print("--- Testing generic file addition with default column ---")
#     dummy_generic_path = Path('data/dummy_generic_list.parquet')
#     dummy_generic_data = pd.DataFrame({'CASRN': ['71-43-2', '123-45-6']})
#     dummy_generic_data.to_parquet(dummy_generic_path, index=False)
#     print(f"Created dummy generic file at '{dummy_generic_path}'")
#     add_casrns_from_file(dummy_generic_path, source_name='Project_Y_List') # No column name needed
    
#     # Verify the final state of the master list
#     final_df = pd.read_parquet(MASTER_FILE_PATH)
#     print("\n--- Final Master List ---")
#     print(final_df)
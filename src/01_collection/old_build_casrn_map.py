import pandas as pd
import json
import os
import time

# Import the existing API client and configuration
import epa_api_client as eac
import config

# <-- Batch size removed, pivoting to single-item lookups
# BATCH_SIZE = 100

def find_casrn_column(df):
    """
    Attempts to find the CASRN column in the DataFrame, checking common variations.
    """
    possible_cols = ['CASRN', 'casrn', 'cas_rn', 'CAS_RN', 'CAS Number']
    for col in possible_cols:
        if col in df.columns:
            print(f"Found CASRN column: '{col}'")
            return col
    print(f"Error: Could not find a CASRN column in the input file.")
    print(f"Looked for: {possible_cols}")
    print(f"Found columns: {df.columns.tolist()}")
    return None

def build_translation_table():
    """
    Reads the master CASRN list, queries the EPA API *one by one*
    to find matching DTXSIDs, and saves the resulting map to a JSON file.
    
    NOTE: This is the fallback method and will be slow.
    """
    print(f"Loading master list from: {config.MASTER_CAS_LIST}")
    if not os.path.exists(config.MASTER_CAS_LIST):
        print(f"Error: Master list file not found at {config.MASTER_CAS_LIST}")
        print("Please update the path in config.py")
        return

    try:
        # Read from the parquet file as requested
        df = pd.read_parquet(config.MASTER_CAS_LIST)
    except Exception as e:
        print(f"Error reading parquet file: {e}")
        return
        
    cas_col = find_casrn_column(df)
    if not cas_col:
        return

    # Get a list of unique, non-null CASRNs
    casrn_list = df[cas_col].dropna().unique().tolist()
    total_casrns = len(casrn_list)
    print(f"Found {total_casrns} unique, non-null CASRNs in the master list.")

    if not total_casrns:
        print("No CASRNs to process.")
        return

    # Initialize the map. We will store DTXSIDs in a list
    # to handle potential one-to-many CASRN -> DTXSID relationships.
    translation_map = {}
    
    # <-- Removed batching logic, switching to single-item loop
    print(f"Beginning API processing for {total_casrns} CASRNs (one by one)...")

    for i, casrn_to_check in enumerate(casrn_list):
        
        # Log progress every 25 chemicals
        if (i + 1) % 25 == 0:
            print(f"Processing {i+1} / {total_casrns} (CASRN: {casrn_to_check})...")
        
        try:
            # Call the *single-item* function from the client
            response_data = eac.get_dtxsid_by_casrn(casrn_to_check)
            
            # The API returns a list of matches for a single CASRN
            if not response_data or not isinstance(response_data, list):
                # print(f"No match found for {casrn_to_check}")
                translation_map[casrn_to_check] = []
                continue
                
            # <-- Updated parsing logic for single-item response
            # The response is a list, extract dtxsid from each item
            
            dtxsids_found = []
            for item in response_data:
                dtxsid = item.get('dtxsid')
                if dtxsid:
                    dtxsids_found.append(dtxsid)
            
            if dtxsids_found:
                translation_map[casrn_to_check] = dtxsids_found
            else:
                translation_map[casrn_to_check] = []
            
        except Exception as e:
            print(f"An error occurred while processing {casrn_to_check}: {e}")
            translation_map[casrn_to_check] = [] # Log as error/empty
            
        # Add a small delay to be kind to the API
        time.sleep(0.1) # 10 requests per second max

    # --- Save the map ---
    output_file = config.CASRN_DTXSID_MAP_OUTPUT
    output_dir = os.path.dirname(output_file)
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print(f"Created output directory: {output_dir}")

    print(f"\nAPI queries complete. Saving translation map to {output_file}...")
    
    try:
        with open(output_file, 'w') as f:
            json.dump(translation_map, f, indent=2)
        print(f"Successfully saved map with {len(translation_map)} entries.")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

if __name__ == "__main__":
    build_translation_table()
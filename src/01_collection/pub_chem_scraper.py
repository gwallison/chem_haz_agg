# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 09:54:41 2025
Refactored on Mon Aug 25 16:10:03 2025
Refactored on Thu Sep 04 07:13:00 2025

@author: Gary
"""
import pandas as pd
import requests
import time
import json
from pathlib import Path
import re

# Import the master file path from your manager module.
from master_list_manager import MASTER_FILE_PATH

# Define paths for the primary data output and the debug file
PUBCHEM_OUTPUT_PATH = MASTER_FILE_PATH.parent / 'pubchem_ghs_hazards.parquet'
DEBUG_OUTPUT_PATH = MASTER_FILE_PATH.parent / 'debug_output.json'


def get_cid_from_cas(cas_rn, session, verbose=False):
    """Queries PubChem to get the Compound ID (CID) for a given CAS RN."""
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/cids/JSON"
    request_url = base_url.format(cas_rn)
    try:
        response = session.get(request_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "IdentifierList" in data and "CID" in data["IdentifierList"]:
            return data["IdentifierList"]["CID"][0]
        return None
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        if verbose: print(f"  - Error fetching CID for {cas_rn}: {e}")
        else: print('_', end='')
        return None

def find_ghs_data_recursively(sections):
    """
    Recursively searches through PubChem's JSON structure to find and extract
    GHS Hazard Statements (H-codes), Pictogram codes, Signal words, and
    Precautionary Statement Codes (P-codes).
    """
    found_data = {
        "h_codes": set(), "pictograms": set(), "signals": set(), "p_codes": set()
    }

    for section in sections:
        for info in section.get("Information", []):
            name = info.get("Name", "").strip()
            value_list = info.get("Value", {}).get("StringWithMarkup", [])

            if name == "GHS Hazard Statements":
                for item in value_list:
                    h_string = item.get("String")
                    if h_string:
                        match = re.match(r'H\d{3,}', h_string)
                        if match:
                            found_data["h_codes"].add(match.group(0))

            elif name == "Pictogram(s)":
                for item in value_list:
                    for markup in item.get("Markup", []):
                        url = markup.get("URL")
                        if url and "ghs" in url and markup.get("Type") == "Icon":
                            p_code = url.split('/')[-1].split('.')[0]
                            if p_code.startswith("GHS"):
                                found_data["pictograms"].add(p_code)

            elif name == "Signal":
                for item in value_list:
                    s_string = item.get("String")
                    if s_string:
                        found_data["signals"].add(s_string.strip())

            elif name == "Precautionary Statement Codes":
                for item in value_list:
                    p_string = item.get("String")
                    if p_string:
                        codes = re.findall(r'P\d+(?:\+P\d+)*', p_string)
                        if codes:
                            found_data["p_codes"].update(codes)

        if "Section" in section:
            deeper_data = find_ghs_data_recursively(section["Section"])
            found_data["h_codes"].update(deeper_data["h_codes"])
            found_data["pictograms"].update(deeper_data["pictograms"])
            found_data["signals"].update(deeper_data["signals"])
            found_data["p_codes"].update(deeper_data["p_codes"])

    return found_data

def get_ghs_data_from_cid(cid, session, verbose=False):
    """
    Queries PubChem's GHS section for a given CID and extracts H-codes,
    pictograms, signal words, and P-codes.
    """
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{}/JSON/?heading=GHS+Classification"
    request_url = base_url.format(cid)
    try:
        response = session.get(request_url, timeout=15)
        response.raise_for_status()
        data = response.json()
        root_sections = data.get("Record", {}).get("Section", [])
        ghs_data = find_ghs_data_recursively(root_sections)
        return {
            "h_codes": sorted(list(ghs_data["h_codes"])),
            "pictograms": sorted(list(ghs_data["pictograms"])),
            "signals": sorted(list(ghs_data["signals"])),
            "p_codes": sorted(list(ghs_data["p_codes"]))
        }
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        if verbose: print(f"  - Error fetching GHS for CID {cid}: {e}")
        else: print('-', end='')
        return {"h_codes": [], "pictograms": [], "signals": [], "p_codes": []}

def run_pubchem_update(verbose: bool = False):
    """
    Reads the master CASRN list, fetches missing PubChem GHS data, and saves results.
    """
    print('--- Starting PubChem GHS code update ---')

    print(f"Reading master list from: {MASTER_FILE_PATH}")
    if not MASTER_FILE_PATH.exists():
        print(f"❌ Error: Master list not found.")
        return
    master_df = pd.read_parquet(MASTER_FILE_PATH)
    master_cas_list = master_df['CASRN'].astype(str).str.strip().unique().tolist()

    print(f"Checking for existing PubChem data at: {PUBCHEM_OUTPUT_PATH}")
    existing_df = pd.DataFrame()

    if PUBCHEM_OUTPUT_PATH.exists():
        try:
            existing_df = pd.read_parquet(PUBCHEM_OUTPUT_PATH)
        except Exception as e:
            print(f"⚠️  Could not read existing file due to an error: {e}. Processing all records.")
    else:
        print("No existing PubChem data file found. Will process all records.")

    schema_changed = False
    required_cols = ['CASRN', 'PubChem_CID', 'GHS_H_Codes', 'GHS_Pictograms', 'GHS_Signals', 'GHS_P_Codes', 'Download_Date']
    for col in required_cols:
        if col not in existing_df.columns:
            print(f"⚠️  Adding missing column '{col}' to accommodate old data file schema.")
            existing_df[col] = 'N/A' if col != 'Download_Date' else time.strftime("%Y-%m-%d")
            schema_changed = True

    processed_cas = set(existing_df['CASRN'].astype(str).str.strip())
    new_cas_list = [cas for cas in master_cas_list if cas not in processed_cas]
    
    cas_to_reprocess = set()
    missing_data_values = ['N/A', 'No GHS Data Found', '']
    for col in ['GHS_Pictograms', 'GHS_Signals', 'GHS_P_Codes']:
        cas_to_reprocess.update(existing_df[existing_df[col].isin(missing_data_values)]['CASRN'].tolist())
    
    cas_to_process = sorted(list(set(new_cas_list).union(cas_to_reprocess)))
    
    df_to_keep = existing_df[~existing_df['CASRN'].isin(cas_to_process)].copy()

    print("\n--------------------------------------------------")
    print(f"📊 SUMMARY:")
    print(f"   Total unique chemicals in master list: {len(master_cas_list)}")
    print(f"   Chemicals already fully processed:   {len(df_to_keep)}")
    print(f"   Chemicals to process (new + update): {len(cas_to_process)}")
    print("--------------------------------------------------\n")

    if not cas_to_process:
        print("✅ All CASRNs in the master list are fully processed.")
        if schema_changed:
            print("... Saving file to update schema on disk.")
            df_to_keep.to_parquet(PUBCHEM_OUTPUT_PATH, index=False)
        return
    
    total_to_process = len(cas_to_process)
    batch_size = 10
    newly_processed_batch = []
    final_df = df_to_keep.copy()

    with requests.Session() as session:
        for index, cas_rn in enumerate(cas_to_process, 1):
            if verbose: print(f"\nProcessing ({index}/{total_to_process}): {cas_rn}")
            else: print(':', end='')
            
            time.sleep(0.5)
            cid = get_cid_from_cas(cas_rn, session, verbose)
            
            result = {}
            if cid:
                time.sleep(0.25)
                ghs_data = get_ghs_data_from_cid(cid, session, verbose)
                result = {
                    'CASRN': cas_rn, 'PubChem_CID': cid, 
                    'GHS_H_Codes': ', '.join(ghs_data['h_codes']) or "No GHS Data Found",
                    'GHS_Pictograms': ', '.join(ghs_data['pictograms']) or "No GHS Data Found",
                    'GHS_Signals': ', '.join(ghs_data['signals']) or "No GHS Data Found",
                    'GHS_P_Codes': ', '.join(ghs_data['p_codes']) or "No GHS Data Found",
                    'Download_Date': time.strftime("%Y-%m-%d")
                }
            else:
                result = {
                    'CASRN': cas_rn, 'PubChem_CID': -1, 
                    'GHS_H_Codes': 'N/A', 'GHS_Pictograms': 'N/A',
                    'GHS_Signals': 'N/A', 'GHS_P_Codes': 'N/A',
                    'Download_Date': time.strftime("%Y-%m-%d")
                }
            newly_processed_batch.append(result)

            if (index % batch_size == 0 or index == total_to_process) and newly_processed_batch:
                if verbose: print(f"\n--- Saving batch of {len(newly_processed_batch)} records ---")
                else: print('S', end='')
                
                batch_df = pd.DataFrame(newly_processed_batch)
                final_df = pd.concat([final_df, batch_df], ignore_index=True)
                final_df.to_parquet(PUBCHEM_OUTPUT_PATH, index=False)
                newly_processed_batch = []

    print(f"\n✅ Processing complete. All results saved to '{PUBCHEM_OUTPUT_PATH}'")

def debug_single_cas(cas_to_debug):
    """Fetches full GHS JSON for a single CAS and saves it for inspection."""
    print(f"\n--- Starting Debug Mode for CAS: {cas_to_debug} ---")
    with requests.Session() as session:
        cid = get_cid_from_cas(cas_to_debug, session, verbose=True)
        if not cid:
            print("Could not find CID. Aborting debug.")
            return
        
        base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{}/JSON/?heading=GHS+Classification"
        request_url = base_url.format(cid)
        print(f"Fetching data from: {request_url}")
        
        try:
            response = session.get(request_url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            with open(DEBUG_OUTPUT_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            print(f"\nSUCCESS: Raw JSON response saved to '{DEBUG_OUTPUT_PATH}'")
            
            print("\nAttempting to parse the saved data...")
            ghs_data = find_ghs_data_recursively(data.get("Record", {}).get("Section", []))
            if any(ghs_data.values()):
                print(f"SUCCESS: Found H-Codes: {sorted(list(ghs_data['h_codes']))}")
                print(f"SUCCESS: Found Pictograms: {sorted(list(ghs_data['pictograms']))}")
                print(f"SUCCESS: Found Signals: {sorted(list(ghs_data['signals']))}")
                print(f"SUCCESS: Found P-Codes: {sorted(list(ghs_data['p_codes']))}")
            else:
                print("FAILURE: Parsing logic failed to find any GHS data.")
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"An error occurred during debug: {e}")


# --- Main Execution ---
if __name__ == "__main__":
    # run_pubchem_update(verbose=False)
    debug_single_cas('100545-50-4') 


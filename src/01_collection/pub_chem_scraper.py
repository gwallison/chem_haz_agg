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
import os
from requests.exceptions import HTTPError, RequestException, JSONDecodeError # <-- Import more specific exceptions

# Import the master file path from your manager module.
# from master_list_manager import MASTER_FILE_PATH
from config import MASTER_CAS_LIST, PUBCHEM_OUTPUT_PATH


def make_polite_request(url, session, max_retries=3, initial_sleep=5, verbose=False):
    """
    Makes a 'polite' request that handles 503/429 throttling errors
    by using exponential backoff.
    """
    retries = 0
    while retries < max_retries:
        try:
            response = session.get(url, timeout=15)
            # Raise an error for bad status codes (like 503 or 429)
            response.raise_for_status() 
            
            # If successful, return the JSON data
            return response.json() 

        except HTTPError as e:
            # Check if this is a throttling error
            if e.response.status_code in [503, 429]:
                retries += 1
                sleep_time = initial_sleep * (2 ** retries) # Exponential backoff
                
                if verbose:
                    print(f"\n  - Received {e.response.status_code}. Throttled. "
                          f"Waiting {sleep_time}s before retry {retries}/{max_retries}...")
                else:
                    print('W', end='')
                
                time.sleep(sleep_time)
            else:
                # It's a different HTTP error (e.g., 404 Not Found), so don't retry.
                if verbose: print(f"  - HTTP Error (non-retryable): {e}")
                else: print('E', end='')
                return None # Fail the request
                
        except (RequestException, JSONDecodeError) as e:
            # General connection error or bad JSON
            if verbose: print(f"  - Request/JSON Error: {e}")
            else: print('X', end='')
            return None # Fail the request
    
    if verbose: print(f"  - Max retries exceeded for {url}")
    return None # Failed after all retries

import pubchempy as pcp

# def get_cid_with_pubchempy(casrn):
#     """
#     Fetches CID using the pubchempy library.
#     It handles rate limiting automatically.
#     """
#     try:
#         # 'cas' is the namespace for CASRN
#         compounds = pcp.get_compounds(casrn, 'cas')
#         if compounds:
#             # Return the first compound's CID
#             return compounds[0].cid
#         else:
#             return None
#     except Exception as e:
#         # Handles various lookup errors
#         print(f"Error looking up {casrn}: {e}")
#         return None


# def get_cid_from_cas(cas_rn, session, verbose=False):
#     """Queries PubChem to get the Compound ID (CID) for a given CAS RN."""
#     base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/cids/JSON"
#     request_url = base_url.format(cas_rn)
#     try:
#         response = session.get(request_url, timeout=10)
#         response.raise_for_status()
#         data = response.json()
#         if "IdentifierList" in data and "CID" in data["IdentifierList"]:
#             return data["IdentifierList"]["CID"][0]
#         return None
#     except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
#         if verbose: print(f"  - Error fetching CID for {cas_rn}: {e}")
#         else: print('_', end='')
#         return None

def get_cid_from_cas(cas_rn, session, verbose=False):
    """Queries PubChem to get the Compound ID (CID) for a given CAS RN."""
    base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/cids/JSON"
    request_url = base_url.format(cas_rn)
    
    data = make_polite_request(request_url, session, verbose=verbose)
    
    if data and "IdentifierList" in data and "CID" in data["IdentifierList"]:
        return data["IdentifierList"]["CID"][0]
        
    if verbose: print(f"  - No CID found for {cas_rn}")
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
    print(request_url)
    data = make_polite_request(request_url, session, verbose=verbose)

    if data:
        root_sections = data.get("Record", {}).get("Section", [])
        ghs_data = find_ghs_data_recursively(root_sections)
        return {
            "h_codes": sorted(list(ghs_data["h_codes"])),
            "pictograms": sorted(list(ghs_data["pictograms"])),
            "signals": sorted(list(ghs_data["signals"])),
            "p_codes": sorted(list(ghs_data["p_codes"]))
        }
    
    if verbose: print(f"  - Error fetching GHS for CID {cid}")
    else: print('-', end='')
    return {"h_codes": [], "pictograms": [], "signals": [], "p_codes": []}

def run_pubchem_update(verbose: bool = False):
    """
    Reads the master CASRN list, fetches missing PubChem GHS data, and saves results.
    """
    print('--- Starting PubChem GHS code update ---')

    print(f"Reading master list from: {MASTER_CAS_LIST}")
    if not os.path.exists(MASTER_CAS_LIST):
        print(f"❌ Error: Master list not found.")
        return
    master_df = pd.read_parquet(MASTER_CAS_LIST)
    master_cas_list = master_df['CASRN'].astype(str).str.strip().unique().tolist()

    # master_cas_list = ['111-42-2']

    print(f"Checking for existing PubChem data at: {PUBCHEM_OUTPUT_PATH}")
    existing_df = pd.DataFrame()

    if os.path.exists(PUBCHEM_OUTPUT_PATH):
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
    
    #####
    # cas_to_process = ['50-00-0']
    ######
    
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
            
            # time.sleep(0.5)
            cid = get_cid_from_cas(cas_rn, session, verbose)
            
            result = {}
            if cid:
                # time.sleep(0.25)
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


            # OPTIONAL: You can add a single, small, static sleep here 
            # at the *end* of the loop, just to be a good citizen.
            # This is independent of the reactive throttling, which is
            # now your primary defense.
            time.sleep(0.2) # e.g., to stay under 5 requests/sec
            
    print(f"\n✅ Processing complete. All results saved to '{PUBCHEM_OUTPUT_PATH}'")



# --- Main Execution ---
if __name__ == "__main__":
    run_pubchem_update(verbose=False)
    # print(get_cid_with_pubchempy('50-00-0'))


# -*- coding: utf-8 -*-
"""
Created on Wed Feb  4 08:18:02 2026

@author: Gary

This file contains functions to bulk harvest the results of API requests
from the EPA facility.  Results are stored locally.
"""

import os
import numpy as np
import json
import time
import pandas as pd
import epa_api_client as eac  # Assuming this handles the Hazard API calls
import config
import master_list_manager as mlm

def harvest_toxval_data():
    """
    Harvests ToxVal JSON records from the EPA Hazard API and saves them locally.
    Filenames are formatted as: toxval_{CASRN}.json
    """
    # 1. Ensure the output directory exists
    os.makedirs(config.EPA_HAZ_TOXVAL_JSON_DIR, exist_ok=True)
    
    # 2. Get master chemical list
    mastcasdf = mlm.get_master_df()
    
    # 3. Filter for chemicals we haven't harvested yet
    # Check existing files in the directory to avoid duplicates
    existing_files = os.listdir(config.EPA_HAZ_TOXVAL_JSON_DIR)
    processed_casrns = {f.replace("toxval_", "").replace(".json", "") for f in existing_files}
    
    work_df = mastcasdf[~mastcasdf['CASRN'].isin(processed_casrns)].copy()
    print(f"Total chemicals in master: {len(mastcasdf)}")
    print(f"Remaining to harvest: {len(work_df)}")

    for _, row in work_df.iterrows():
        casrn = row['CASRN']
        dtxsids = row['DTXSIDs']
        
        # 1. Clean the list: Handle cases where dtxsids is a list containing a numpy array
        clean_ids = []
        if isinstance(dtxsids, (list, pd.Series, np.ndarray)):
            for item in dtxsids:
                # If it's a numpy array, extract the string inside
                if isinstance(item, np.ndarray):
                    clean_ids.extend(item.flatten().tolist())
                else:
                    clean_ids.append(item)
        else:
            clean_ids = [dtxsids]

        all_data = []
        for dtxsid in clean_ids:
            if pd.isna(dtxsid) or not dtxsid:
                continue
            
            # 2. Final sanitization: convert to string and strip
            dtxsid_str = str(dtxsid).strip()
            
            # Optional: Add a safety check to ensure it looks like a DTXSID
            if not dtxsid_str.startswith("DTXSID"):
                continue

            response_json = eac.get_hazard_details(dtxsid_str)
            
            if response_json:
                if isinstance(response_json, list):
                    all_data.extend(response_json)
                else:
                    all_data.append(response_json)

        # Ensure the output path is defined
        out_path = os.path.join(config.EPA_HAZ_TOXVAL_JSON_DIR, f"toxval_{casrn}.json")

        # Always save the file to "mark" it as processed
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=4)
        
        # Log the result for visibility
        if all_data:
            print(f"SUCCESS: Saved {casrn} ({len(all_data)} records)")
        else:
            print(f"ABSENCE: Saved empty placeholder for {casrn}")        # Respectful throttling

        time.sleep(5)

def harvest_chem_data():
    """
    Harvests full JSON records from the EPA Chemical API and saves them locally.
    Filenames are formatted as: chemical_{CASRN}.json
    """
    # 1. Ensure the output directory exists
    os.makedirs(config.EPA_CHEM_API_JSON_DIR, exist_ok=True)
    
    # 2. Get master chemical list
    mastcasdf = mlm.get_master_df()
    
    # 3. Filter for chemicals we haven't harvested yet
    # Check existing files in the directory to avoid duplicates
    existing_files = os.listdir(config.EPA_CHEM_API_JSON_DIR)
    processed_casrns = {f.replace("chemical_", "").replace(".json", "") for f in existing_files}
    
    work_df = mastcasdf[~mastcasdf['CASRN'].isin(processed_casrns)].copy()
    print(f"Total chemicals in master: {len(mastcasdf)}")
    print(f"Remaining to harvest: {len(work_df)}")

    for _, row in work_df.iterrows():
        casrn = row['CASRN']
        dtxsids = row['DTXSIDs']
        
        # 1. Clean the list: Handle cases where dtxsids is a list containing a numpy array
        clean_ids = []
        if isinstance(dtxsids, (list, pd.Series, np.ndarray)):
            for item in dtxsids:
                # If it's a numpy array, extract the string inside
                if isinstance(item, np.ndarray):
                    clean_ids.extend(item.flatten().tolist())
                else:
                    clean_ids.append(item)
        else:
            clean_ids = [dtxsids]

        all_data = []
        for dtxsid in clean_ids:
            if pd.isna(dtxsid) or not dtxsid:
                continue
            
            # 2. Final sanitization: convert to string and strip
            dtxsid_str = str(dtxsid).strip()
            
            # Optional: Add a safety check to ensure it looks like a DTXSID
            if not dtxsid_str.startswith("DTXSID"):
                continue

            response_json = eac.get_chemical_details(dtxsid_str)
            
            if response_json:
                if isinstance(response_json, list):
                    all_data.extend(response_json)
                else:
                    all_data.append(response_json)

        # Ensure the output path is defined
        out_path = os.path.join(config.EPA_CHEM_API_JSON_DIR, f"chemical_{casrn}.json")

        # Always save the file to "mark" it as processed
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=4)
        
        # Log the result for visibility
        if all_data:
            print(f"SUCCESS: Saved {casrn} ")
        else:
            print(f"ABSENCE: Saved empty placeholder for {casrn}")        # Respectful throttling

        time.sleep(2.5)

if __name__ == "__main__":
    # harvest_toxval_data()
    harvest_chem_data()
    
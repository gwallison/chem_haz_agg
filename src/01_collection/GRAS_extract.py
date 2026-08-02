# -*- coding: utf-8 -*-
"""
Created on Sun Jan  4 13:02:22 2026

@author: Gary
"""

import requests
import pandas as pd
import re
import os
import sys

# Add the project root to the Python path to resolve the 'config' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config

def download_and_extract_gras():
    """
    Downloads the SCOGS GRAS list from the FDA, extracts Chemical Name and CASRN,
    and saves the output as a Parquet file.
    """
    url = "https://hfpappexternal.fda.gov/scripts/fdcc/cfc/XMLService.cfm?method=downloadxls&set=SCOGS"
    
    # 1. Download the file
    print(f"Downloading file from {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Save raw file
        with open(config.RAW_GRAS_DETAILS, 'wb') as f:
            f.write(response.content)
        print(f"Raw file saved to: {config.RAW_GRAS_DETAILS}")
        
    except Exception as e:
        print(f"Failed to download file: {e}")
        return

    # 2. Extract data
    # Based on the provided CSV, skipping 4 rows correctly aligns the header 
    # 'GRAS Substance' (which is on line 5 of the raw file).
    try:
        df = pd.read_csv(config.RAW_GRAS_DETAILS, skiprows=4)
        
        # Define the mapping based on the FDA CSV structure
        column_mapping = {
            'GRAS Substance': 'Chemical_Name',
            'CAS Reg. No. or other ID CODE': 'CASRN'
        }
        
        # Verify columns exist before processing
        missing_cols = [c for c in column_mapping.keys() if c not in df.columns]
        if missing_cols:
            raise KeyError(f"Missing expected columns in CSV: {missing_cols}")
            
        # Select and rename columns
        df = df[list(column_mapping.keys())].rename(columns=column_mapping)
        
        # 3. Clean data
        # FDA exports often wrap values in =T("...") formulas for Excel compatibility.
        def clean_excel_artifacts(val):
            if not isinstance(val, str):
                return val
            # Remove =T("...") wrappers and strip whitespace
            cleaned = re.sub(r'^=T\("(.*)"\)$', r'\1', val)
            return cleaned.strip()

        df['Chemical_Name'] = df['Chemical_Name'].apply(clean_excel_artifacts)
        df['CASRN'] = df['CASRN'].apply(clean_excel_artifacts)
        
        # Remove any rows where both are null (common at end of file)
        df = df.dropna(how='all')

        # 4. Save as Parquet
        df.to_parquet(config.GRAS_DETAILS, index=False)
        print(f"Successfully saved {len(df)} records to: {config.GRAS_DETAILS}")
        
    except Exception as e:
        print(f"Error processing the CSV file: {e}")

# Usage assumes a config object with RAW_GRAS_DETAILS and GRAS_DETAILS paths
if __name__ == "__main__":
    download_and_extract_gras()
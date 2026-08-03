# -*- coding: utf-8 -*-
"""
Created on Fri Aug 29 10:06:46 2025
Refactored on Thu Sep 04 14:25:00 2025

@author: Gary

Translates an Excel file downloaded from Safe Work Australia to a standardized
Parquet format that is compatible with other GHS data sources.
"""

import pandas as pd
# from pathlib import Path
import time
# import re
import os
import sys

# Add the project root to the Python path to resolve the 'config' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config

# It's good practice to define paths relative to the script's location.
# This assumes your 'data' folder is a child of the 'code' folder.


def get_input_file():
    lst = os.listdir(config.RAW_DATA)
    aus_files = []
    for fn in lst:
        if fn.startswith('HCIS_Chemical_Data_'):
            if fn.endswith('.xlsx'):
                aus_files.append(fn)
    aus_files.sort()
    return os.path.join(config.RAW_DATA, aus_files[-1])


def process_australia_data():
    """
    Reads the Safe Work Australia Excel file, processes it into a standard GHS
    format, and saves it as a Parquet file.
    """
    print("--- Starting Safe Work Australia data processing ---")
    input_file = get_input_file()
    if not os.path.exists(input_file):
        print(f"❌ Error: Input file not found at '{input_file}'")
        return None

    print(f"Reading data from: {input_file}")
    df = pd.read_excel(input_file, skiprows=4)

    # 1. Clean up CASRN and filter out records without one.
    df.rename(columns={'CAS': 'CASRN'}, inplace=True)
    df.dropna(subset=['CASRN'], inplace=True)
    df['CASRN'] = df['CASRN'].astype(str).str.strip()

    # 2. Combine Health + Physical hazard statement codes into one field.
    def combine_h_codes(row):
        codes = []
        for col in ['Health Hazard Statement Codes', 'Physical Hazard Statement Codes']:
            val = row[col]
            if isinstance(val, str) and val.strip():
                codes.extend(p.strip() for p in val.replace(';', ',').split(','))
        return ', '.join(codes) if codes else 'N/A'

    df['GHS_H_Codes'] = df.apply(combine_h_codes, axis=1)

    # 3. Pictogram codes and signal word are now their own columns.
    df['GHS_Pictograms'] = df['Pictogram Codes'].astype(str).str.strip().replace('nan', 'N/A')
    df['GHS_Signals'] = df['Signal Word'].astype(str).str.strip().replace('nan', 'N/A')

    # 4. Add placeholder columns to match the PubChem schema.
    df['GHS_P_Codes'] = 'N/A'
    df['Download_Date'] = time.strftime("%Y-%m-%d")

    # 5. Select and order columns for the final output.
    final_columns = [
        'CASRN', 'GHS_H_Codes', 'GHS_Pictograms', 
        'GHS_Signals', 'GHS_P_Codes', 'Download_Date'
    ]
    output_df = df[final_columns]
    
    # 6. Save the standardized data to a Parquet file.
    output_df.to_parquet(config.AUS_OUTPUT_PATH, index=False)
    print(f"✅ Processing complete. Results saved to '{config.AUS_OUTPUT_PATH}'")
    
    return output_df

if __name__ == '__main__':
    processed_df = process_australia_data()
    if processed_df is not None:
        print("\n--- Sample of Processed Data ---")
        print(processed_df.head())


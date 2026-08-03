# -*- coding: utf-8 -*-
"""
Created on Thu Sep 04 17:00:00 2025

@author: Gary

Processes an Excel file from the Japan NITE GHS database, translating its
category-based classifications into standard GHS H-codes. The output is a 
Parquet file with a schema compatible with other GHS data scrapers.
"""
import pandas as pd
from pathlib import Path
import time
import os
import sys
import datetime

# Add the project root to the Python path to resolve the 'config' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config


# --- Configuration ---


modtime = os.path.getmtime(config.JAPAN_INPUT_XLSX)
filemod = datetime.datetime.fromtimestamp(modtime)

# This dictionary is the core of the translation. It maps the exact column
# names from the Excel file to a sub-dictionary that translates category
# strings into the corresponding GHS H-codes.
GHS_CATEGORY_TO_H_CODE_MAPPING = {
    'Acute toxicity （Oral）': {'Category 1': 'H300', 'Category 2': 'H300', 'Category 3': 'H301', 'Category 4': 'H302', 'Category 5': 'H303'},
    'Acute toxicity （Dermal）': {'Category 1': 'H310', 'Category 2': 'H310', 'Category 3': 'H311', 'Category 4': 'H312', 'Category 5': 'H313'},
    'Acute toxicity （Inhalation: Gases）': {'Category 1': 'H330', 'Category 2': 'H330', 'Category 3': 'H331', 'Category 4': 'H332', 'Category 5': 'H333'},
    'Acute toxicity （Inhalation: Vapours）': {'Category 1': 'H330', 'Category 2': 'H330', 'Category 3': 'H331', 'Category 4': 'H332', 'Category 5': 'H333'},
    'Acute toxicity （Inhalation: Dusts and mists）': {'Category 1': 'H330', 'Category 2': 'H330', 'Category 3': 'H331', 'Category 4': 'H332', 'Category 5': 'H333'},
    'Skin corrosion/irritation': {'Category 1': 'H314', 'Category 1A': 'H314', 'Category 1B': 'H314', 'Category 1C': 'H314', 'Category 2': 'H315', 'Category 3': 'H316'},
    'Serious eye damage/eye irritation': {'Category 1': 'H318', 'Category 2': 'H319', 'Category 2A': 'H319', 'Category 2B': 'H320'},
    'Respiratory sensitization': {'Category 1': 'H334', 'Category 1A': 'H334', 'Category 1B': 'H334'},
    'Skin sensitization': {'Category 1': 'H317', 'Category 1A': 'H317', 'Category 1B': 'H317'},
    'Germ cell mutagenicity': {'Category 1': 'H340', 'Category 1A': 'H340', 'Category 1B': 'H340', 'Category 2': 'H341'},
    'Carcinogenicity': {'Category 1': 'H350', 'Category 1A': 'H350', 'Category 1B': 'H350', 'Category 2': 'H351'},
    'Reproductive toxicity': {'Category 1': 'H360', 'Category 1A': 'H360', 'Category 1B': 'H360', 'Category 2': 'H361', 'Effects on or via lactation': 'H362'},
    'Specific target organ toxicity - Single exposure': {'Category 1': 'H370', 'Category 2': 'H371', 'Category 3': 'H335'}, # H335 is for Respiratory Tract Irritation, a common Cat 3 endpoint.
    'Specific target organ toxicity - Repeated exposure': {'Category 1': 'H372', 'Category 2': 'H373'},
    'Aspiration hazard': {'Category 1': 'H304'},
    'Hazardous to the aquatic environment （Acute）': {'Category 1': 'H400', 'Category 2': 'H401', 'Category 3': 'H402'},
    'Hazardous to the aquatic environment （Long-term）': {'Category 1': 'H410', 'Category 2': 'H411', 'Category 3': 'H412', 'Category 4': 'H413'},
    'Hazardous to the ozone layer': {'Category 1': 'H420'},
}

def translate_row_to_h_codes(row, hazard_columns_map):
    """
    Takes a DataFrame row and translates its GHS categories into a list of H-codes.
    """
    h_codes = set()
    for column_name, category_map in hazard_columns_map.items():
        if column_name in row.index:
            category_value = str(row[column_name]).strip()
            # Look up the H-code if the category value is in our map
            if category_value in category_map:
                h_codes.add(category_map[category_value])
    return sorted(list(h_codes))

def process_japan_data():
    """
    Reads the Japan NITE GHS Excel file, translates classifications to H-codes,
    and saves the standardized data to a Parquet file.
    """
    print("--- Starting Japan NITE GHS data processing ---")
    if not os.path.exists(config.JAPAN_INPUT_XLSX):
        print(f"❌ Error: Input file not found at '{config.JAPAN_INPUT_XLSX}'")
        return None

    print(f"Reading data from: {config.JAPAN_INPUT_XLSX}")
    df = pd.read_excel(config.JAPAN_INPUT_XLSX)

    # 1. Clean up CASRN and filter out records without one.
    df.rename(columns={'CAS RN': 'CASRN'}, inplace=True)
    df.dropna(subset=['CASRN'], inplace=True)
    df['CASRN'] = df['CASRN'].astype(str).str.strip()

    # 2. Translate the category columns into a list of H-codes for each individual row.
    print("Translating GHS categories to H-codes...")
    df['h_code_list'] = df.apply(lambda row: translate_row_to_h_codes(row, GHS_CATEGORY_TO_H_CODE_MAPPING), axis=1)

    # --- NEW: Group by CASRN and aggregate the H-codes ---
    print("Aggregating H-codes for duplicate CASRNs...")
    # This groups all rows for a single CASRN, collects their h_code_lists,
    # flattens them into a single list, finds the unique codes, and sorts them.
    aggregated_df = df.groupby('CASRN')['h_code_list'].apply(
        lambda lists: sorted(list(set(code for sublist in lists for code in sublist)))
    ).reset_index()

    # 3. Convert the final, aggregated list of H-codes into a comma-separated string.
    aggregated_df['GHS_H_Codes'] = aggregated_df['h_code_list'].apply(lambda codes: ', '.join(codes) if codes else 'No GHS Data Found')

    # 4. Add placeholder columns to match the standard schema.
    aggregated_df['GHS_Pictograms'] = 'N/A'
    aggregated_df['GHS_Signals'] = 'N/A'
    aggregated_df['GHS_P_Codes'] = 'N/A'
    aggregated_df['Download_Date'] = filemod.strftime("%Y-%m-%d")

    # 5. Select and order columns for the final, standardized output.
    final_columns = [
        'CASRN', 'GHS_H_Codes', 'GHS_Pictograms',
        'GHS_Signals', 'GHS_P_Codes', 'Download_Date'
    ]
    output_df = aggregated_df[final_columns]
    
    # 6. Save the standardized data to a Parquet file.
    output_df.to_parquet(config.JAPAN_OUTPUT_PATH, index=False)
    print(f"✅ Processing complete. Standardized data saved to '{config.JAPAN_OUTPUT_PATH}'")
    
    return output_df

if __name__ == '__main__':
    processed_df = process_japan_data()
    if processed_df is not None:
        print("\n--- Sample of Processed Data ---")
        # Display a sample of chemicals that have translated codes.
        print(processed_df[processed_df['GHS_H_Codes'] != 'No GHS Data Found'].head())


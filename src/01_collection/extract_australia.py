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
import config

# It's good practice to define paths relative to the script's location.
# This assumes your 'data' folder is a child of the 'code' folder.


def parse_pictograms_and_signals(text):
    """
    Parses a string containing GHS pictograms and signal words separated by semicolons.
    
    Args:
        text (str): The string from the 'Pictogram Codes and Signal Word' column.

    Returns:
        tuple: A tuple containing two strings: a comma-separated list of pictograms
               and a comma-separated list of signal words.
    """
    if not isinstance(text, str):
        return "N/A", "N/A"

    parts = [part.strip() for part in text.split(';')]
    pictograms = sorted([p for p in parts if p.startswith('GHS')])
    signals = sorted([s for s in parts if s in ['Danger', 'Warning']])

    pictograms_str = ', '.join(pictograms) if pictograms else "N/A"
    signals_str = ', '.join(signals) if signals else "N/A"
    
    return pictograms_str, signals_str

def process_australia_data():
    """
    Reads the Safe Work Australia Excel file, processes it into a standard GHS
    format, and saves it as a Parquet file.
    """
    print("--- Starting Safe Work Australia data processing ---")
    if not os.path.exists(config.AUS_INPUT_XLSX):
        print(f"❌ Error: Input file not found at '{config.AUS_INPUT_XLSX}'")
        return None

    print(f"Reading data from: {config.AUS_INPUT_XLSX}")
    df = pd.read_excel(config.AUS_INPUT_XLSX)

    # 1. Clean up CASRN and filter out records without one.
    df.rename(columns={'Cas No': 'CASRN'}, inplace=True)
    df.dropna(subset=['CASRN'], inplace=True)
    df['CASRN'] = df['CASRN'].astype(str).str.strip()
    
    # 2. Extract H-Codes, ensuring they are clean strings.
    df['GHS_H_Codes'] = df['Hazard Statement Codes'].astype(str).str.strip()

    # 3. Parse the combined pictogram and signal word column.
    parsed_data = df['Pictogram Codes and Signal Word'].apply(parse_pictograms_and_signals)
    df[['GHS_Pictograms', 'GHS_Signals']] = pd.DataFrame(parsed_data.tolist(), index=df.index)

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


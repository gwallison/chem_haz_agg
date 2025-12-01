# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 20:42:24 2025

@author: Gary

This script takes the downloaded Excel sheet 
(from https://iris.epa.gov/AtoZ/?list_type=alpha) and
pulls the link, chemical name, and CASRN out to a dataframe.

"""

import pandas as pd
import openpyxl
import os
import config
# --- Please update these variables if needed ---
#EXCEL_FILE_PATH = r"C:\MyDocs\integrated\chem_profiles\data\01_raw\simple_list_alpha.xlsx"
SHEET_NAME = 'simple_list_alpha' 
HYPERLINK_COLUMN_LETTER = 'B'           # The column letter containing the hyperlinks
CHEMICAL_NAME_COLUMN_NAME = 'Chemical Name' # The exact column header for the chemical names
CASRN_COLUMN_NAME = 'CASRN'             # The exact column header for the CASRNs
# ---------------------------------------------

def extract_urls_by_row(file_path, sheet_name, column):
    """
    Uses openpyxl to extract URLs and maps them to their row number.
    """
    try:
        workbook = openpyxl.load_workbook(file_path)
        sheet = workbook[sheet_name]
        
        # Create a dictionary of {row_number: url}
        url_map = {cell.row: cell.hyperlink.target for cell in sheet[column] if cell.hyperlink}
        print(f"Found {len(url_map)} hyperlinks in column {column}.")
        return url_map
        
    except Exception as e:
        print(f"An error occurred with openpyxl: {e}")
        return {}


if __name__ == "__main__":
    # Step 1: Extract the URLs with openpyxl
    urls_by_row = extract_urls_by_row(config.IRIS_EXCEL_FILE_PATH, SHEET_NAME, HYPERLINK_COLUMN_LETTER)

    if urls_by_row:
        # Step 2: Read the Excel file with pandas to get all other data
        print("Reading Excel data with pandas...")
        df = pd.read_excel(config.IRIS_EXCEL_FILE_PATH, sheet_name=SHEET_NAME)
        
        # Step 3: Map the URLs to the DataFrame
        # We add 2 to the DataFrame index to match the 1-based row number in Excel,
        # accounting for the header row.
        df['URL'] = df.index.map(lambda i: urls_by_row.get(i + 2))
        
        # Step 4: Select and rename the final columns
        try:
            final_df = df[[CHEMICAL_NAME_COLUMN_NAME, CASRN_COLUMN_NAME, 'URL']].copy()
            final_df.rename(columns={CHEMICAL_NAME_COLUMN_NAME: 'chemical_name'}, inplace=True)
            
            # Remove rows where a URL could not be found
            final_df.dropna(subset=['URL'], inplace=True)
            
            print("\nDataFrame created successfully. First 5 rows:")
            print(final_df.head())
            
            # Step 5: Save the final DataFrame to a Parquet file
            outdir = config.INTERMED_DATA
            # Updated output filename to be more descriptive
            output_parquet_path = os.path.join(outdir, 'iris_data.parquet')
            
            final_df.to_parquet(output_parquet_path)
            print(f"\nSuccessfully saved the data to '{output_parquet_path}'")
            
        except KeyError as e:
            print(f"\n[ERROR] A column was not found: {e}. Please check your column name settings.")
            print(f"Columns found in the Excel file are: {list(df.columns)}")
            
    else:
        print("\nNo hyperlinks were found, so no output file was created.")
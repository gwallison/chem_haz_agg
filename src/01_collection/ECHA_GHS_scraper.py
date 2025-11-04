""" This script translates ECHA's "Obligation List" into 
a usable set of H-codes for all of the authoritative CASRN.
The source data is a Excel Export from 
"https://chem.echa.europa.eu/obligation-lists/clhList"

"""

# import time
import os
# import re
# from datetime import datetime
import pandas as pd
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, JavascriptException, NoSuchElementException
import config

def get_input_file():
    lst = os.listdir(config.RAW_DATA)
    echa_files = []
    for fn in lst:
        if fn.startswith('Harmonised_List_'):
            if fn.endswith('.xlsx'):
                echa_files.append(fn)
    echa_files.sort()
    return os.path.join(config.RAW_DATA,echa_files[-1])
      
def make_GHS_df():
    rawdf = pd.read_excel(get_input_file())
    # first process all lines keeping track of CASRN and EC Number
    casrns = []
    ecns = []
    hcodes = []
    for i,row in rawdf.iterrows():
        casrns.append(row['CAS number'])
        ecns.append(row['EC number'])
        lst = row['Hazard class, category and statement code(s)'].split('\n')
        s = ''
        for item in lst:
            slst = item.split(',')
            test_str = slst[-1].strip()
            if test_str[0] == 'H':
                s+= test_str +','
        if len(s)>0:
            s = s[:-1] #drop last comma
        hcodes.append(s)
    out = pd.DataFrame({'CASRN':casrns, 'EC_num':ecns,
                        'GHS_H_Codes':hcodes})
    out['GHS_Pictograms'] = ''
    out['GHS_Signals'] = ''
    out['GHS_P_codes'] = ''
    c = ~(out.CASRN.str[0]=='-')
    out = out[c]
    out.to_parquet(config.ECHA_HARM_OUTPUT_PATH)
    
    print(f'Processed and saved {len(out)} CAS records from ECHA')
    print(f'  -- number of duplicate CASRN: {out.CASRN.duplicated().sum()}')
if __name__ == '__main__':
    make_GHS_df()

# # from pathlib import Path

# # Import the master file path from our manager module.
# # from master_list_manager import MASTER_FILE_PATH

# # --- REFACTORED: Define all output paths clearly ---
# # Path for the raw, unprocessed data scraped from the website.
# ECHA_RAW_OUTPUT_PATH = os.path.join(config.INTERMED_DATA,'echa_clp_data.parquet')
# # Path for the final, standardized Harmonized data.
# ECHA_HARM_OUTPUT_PATH = os.path.join(config.INTERMED_DATA, 'echa_harmonized_ghs_hazards.parquet')
# # Path for the final, standardized Industrial (notified) data.
# ECHA_INDUS_OUTPUT_PATH = os.path.join(config.INTERMED_DATA, 'echa_industrial_ghs_hazards.parquet')

# DELAY_BETWEEN_RESULTS = 3

# # --- Saving and Scraping Functions (Unchanged from original script) ---

# def save_data_to_parquet(data_dict):
#     """Appends a dictionary of data to the raw Parquet file."""
#     try:
#         new_df = pd.DataFrame([data_dict])
#         if os.path.exists(ECHA_RAW_OUTPUT_PATH):
#             existing_df = pd.read_parquet(ECHA_RAW_OUTPUT_PATH)
#             combined_df = pd.concat([existing_df, new_df], ignore_index=True)
#         else:
#             combined_df = new_df
#         # os.makedirs(MASTER_FILE_PATH.parent, exist_ok=True)
#         combined_df.to_parquet(ECHA_RAW_OUTPUT_PATH, index=False)
#     except Exception as e:
#         print(f"  - ⚠️ Error saving data to Parquet: {e}")

# def scrape_ghs_data(driver, cas_num, search_ec_num):
#     """Scrapes the GHS classification table from the substance page."""
#     try:
#         ghs_rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
#         if not ghs_rows:
#             save_data_to_parquet({'CASRN': cas_num, 'search_ec_num': search_ec_num, 'classification_type': 'No GHS Table Found'})
#             return

#         for row in ghs_rows:
#             cells = row.find_elements(By.TAG_NAME, 'td')
#             if not cells: continue
            
#             classification_type = cells[0].text.strip()
#             data = {'CASRN': cas_num, 'search_ec_num': search_ec_num, 'classification_type': classification_type}
            
#             if "Harmonised classification" in classification_type:
#                 data['HARM_H-codes'] = cells[1].text.strip()
#                 data['HARM_signal'] = cells[2].text.strip()
#                 data['HARM_GHS-codes'] = cells[3].text.strip()
#             elif "Notified classification" in classification_type:
#                 data['INDUS_H-codes'] = cells[1].text.strip()
#                 data['INDUS_signal'] = cells[2].text.strip()
#                 data['INDUS_GHS-codes'] = cells[3].text.strip()
#             save_data_to_parquet(data)

#     except Exception as e:
#         print(f"  - ⚠️ Error scraping GHS data for {cas_num}: {e}")
#         save_data_to_parquet({'CASRN': cas_num, 'search_ec_num': search_ec_num, 'classification_type': f'Error: {e}'})

# def scrape_substance_page(driver, cas_num):
#     """Navigates to the substance page and initiates scraping."""
#     try:
#         ec_num_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "hexcelEcNo")))
#         search_ec_num = ec_num_element.text
#         scrape_ghs_data(driver, cas_num, search_ec_num)
#     except TimeoutException:
#         print(f"  - No EC number found for {cas_num}, cannot proceed.")
#         save_data_to_parquet({'CASRN': cas_num, 'classification_type': 'No EC Number Found'})

# def main(cas_list):
#     """Main function to drive the scraping process."""
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service)
    
#     processed_cas = set()
#     if os.path.exists(ECHA_RAW_OUTPUT_PATH):
#         try:
#             processed_df = pd.read_parquet(ECHA_RAW_OUTPUT_PATH)
#             processed_cas = set(processed_df['CASRN'].unique())
#             print(f"Resuming. Found {len(processed_cas)} already processed CAS numbers.")
#         except Exception as e:
#             print(f"Could not read existing raw data file: {e}. Starting fresh.")
            
#     cas_to_process = [cas for cas in cas_list if cas not in processed_cas]
#     print(f"Starting to process {len(cas_to_process)} new CAS numbers.")

#     for cas_num in cas_to_process:
#         print(f"Processing CAS: {cas_num}")
#         try:
#             # url = f"https://echa.europa.eu/brief-profile/-/briefprofile/{cas_num}"
#             url = f"https://chem.echa.europa.eu/substance-search?searchText={cas_num}"
#             driver.get(url)
#             scrape_substance_page(driver, cas_num)
#         except Exception as e:
#             print(f"  - ❌ Major error on CAS {cas_num}: {e}")
#             save_data_to_parquet({'CASRN': cas_num, 'classification_type': 'Major Processing Error'})
#         time.sleep(DELAY_BETWEEN_RESULTS)
        
#     driver.quit()
#     print("\n✅ Scraping finished.")

# # --- REFACTORED: New data processing and splitting function ---
# def process_and_split_data():
#     """
#     Reads the raw scraped data, processes it, and saves two separate,
#     standardized Parquet files for Harmonized and Industrial classifications.
#     """
#     print(f"\n--- Starting post-processing of raw data from '{ECHA_RAW_OUTPUT_PATH}' ---")
#     if not os.path.exists(ECHA_RAW_OUTPUT_PATH):
#         print("❌ Raw data file not found. Nothing to process.")
#         return

#     raw_df = pd.read_parquet(ECHA_RAW_OUTPUT_PATH)
    
#     # Get a clean, unique list of all CASRNs from the raw data.
#     all_casrns_df = pd.DataFrame(raw_df['CASRN'].unique(), columns=['CASRN'])

#     def create_standard_df(df, prefix, all_casrns_master_df):
#         """Helper function to create a standardized DataFrame for a given data type."""
        
#         # Define a robust aggregation function to join unique, non-empty strings.
#         def join_unique(series):
#             # Split strings by newline, flatten the list, strip whitespace, remove empty strings, and get unique items.
#             items = set(
#                 item.strip()
#                 for s in series.dropna().astype(str)
#                 for item in s.split('\n')
#                 if item.strip() and item.strip().lower() != 'nan'
#             )
#             return ', '.join(sorted(items)) if items else 'No GHS Data Found'

#         # Select relevant columns for this source type (HARM or INDUS).
#         cols_to_process = ['CASRN'] + [c for c in df.columns if c.startswith(prefix)]
#         source_df = df[cols_to_process].copy().dropna(how='all', subset=cols_to_process[1:])
        
#         if source_df.empty:
#              # If no data for this type exists, create a shell DataFrame for merging.
#             aggregated_df = pd.DataFrame(columns=['CASRN', 'GHS_H_Codes', 'GHS_Signals', 'GHS_Pictograms'])
#         else:
#             # Rename columns to the standard format.
#             rename_map = {
#                 f'{prefix}_H-codes': 'GHS_H_Codes',
#                 f'{prefix}_signal': 'GHS_Signals',
#                 f'{prefix}_GHS-codes': 'GHS_Pictograms'
#             }
#             source_df.rename(columns=rename_map, inplace=True)
            
#             # Aggregate the data for each CASRN.
#             agg_functions = {
#                 'GHS_H_Codes': join_unique,
#                 'GHS_Signals': join_unique,
#                 'GHS_Pictograms': join_unique
#             }
#             aggregated_df = source_df.groupby('CASRN').agg(agg_functions).reset_index()

#         # Merge with the master CASRN list to ensure all are included.
#         merged_df = pd.merge(all_casrns_master_df, aggregated_df, on='CASRN', how='left')
        
#         # Add placeholder columns and fill any missing data.
#         merged_df['GHS_P_Codes'] = 'N/A'
#         merged_df['Download_Date'] = time.strftime("%Y-%m-%d")
        
#         # --- FIX: Changed to a safe, non-inplace method to fill NaNs ---
#         for col in ['GHS_H_Codes', 'GHS_Pictograms', 'GHS_Signals']:
#             merged_df[col] = merged_df[col].fillna('No GHS Data Found')
            
#         # Ensure final column order is correct and compatible with other sources.
#         final_cols = ['CASRN', 'GHS_H_Codes', 'GHS_Pictograms', 'GHS_Signals', 'GHS_P_Codes', 'Download_Date']
#         return merged_df[final_cols]

#     # Create the two separate, standardized DataFrames.
#     print("Processing Harmonized data...")
#     harm_df = create_standard_df(raw_df, 'HARM', all_casrns_df)
    
#     print("Processing Industrial (notified) data...")
#     indus_df = create_standard_df(raw_df, 'INDUS', all_casrns_df)

#     # Save the final standardized files.
#     harm_df.to_parquet(ECHA_HARM_OUTPUT_PATH, index=False)
#     print(f"✅ Harmonized data saved successfully to '{ECHA_HARM_OUTPUT_PATH}'")
    
#     indus_df.to_parquet(ECHA_INDUS_OUTPUT_PATH, index=False)
#     print(f"✅ Industrial data saved successfully to '{ECHA_INDUS_OUTPUT_PATH}'")


# # --- Run the Script ---
# if __name__ == "__main__":
#     # The script is designed to run in two independent steps.
#     # Uncomment the step you want to run.

#     # == STEP 1: Scrape the raw data from the ECHA website ==
#     try:
#         print(f"Reading master CAS list from {config.MASTER_CAS_LIST}...")
#         master_df = pd.read_parquet(config.MASTER_CAS_LIST)
#         cas_to_process = master_df['CASRN'].tolist()
#         print(f'Found {len(cas_to_process)} CASRNs to process in the master list.')
#         main(cas_list=cas_to_process) # Uncomment to run the scraper
#     except FileNotFoundError:
#         print(f"❌ Master CAS list not found at {config.MASTER_CAS_LIST}. Cannot start scraping.")
#     except Exception as e:
#         print(f"An error occurred reading the master list: {e}")

#     # == STEP 2: Process the raw scraped data into standardized files ==
#     process_and_split_data()


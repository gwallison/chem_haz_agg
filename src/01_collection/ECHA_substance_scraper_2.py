# -*- coding: utf-8 -*-
"""
Created on Sun Jan 25 15:24:49 2026

@author: Gary
"""

import pandas as pd
import os
import re
from typing import List, Dict, Any, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import config

# ECHA exports search results under at least two different column-name schemas
# depending on which search UI produced them ("Registered Substances" vs.
# "Search for Chemicals" title row). Normalize the alternate names to the
# canonical ones used everywhere downstream (filter_appropriate_rows, the
# consolidator's record fields) so rows from either schema are recognized.
ALT_COLUMN_NAMES = {
    'Substance Name': 'Name',
    'CAS Number': 'Cas Number',
    'EC Number': 'EC / List Number',
}

def load_chem_links_from_local_csv(file_path: str) -> pd.DataFrame | None:
    """
    Loads a specific, tab-delimited CSV file where the header is on the 3rd row.

    Args:
        file_path (str): The full path to the CSV file.

    Returns:
        pd.DataFrame or None: A DataFrame containing the data from the CSV,
                               or None if an error occurs.
    """
    # Check if the file exists before trying to read it.
    if not os.path.exists(file_path):
        print(f"❌ Error: The file was not found at the specified path: {file_path}")
        return None

    print(f"Attempting to load file: {file_path}")

    try:
        # Read the CSV file using pandas.
        # 'sep=\t' specifies that the file is tab-delimited.
        # 'header=2' tells pandas that the column names are in the 3rd row (since it's 0-indexed).
        df = pd.read_csv(file_path, sep='\t', header=2)
        rename_map = {old: new for old, new in ALT_COLUMN_NAMES.items()
                      if old in df.columns and new not in df.columns}
        if rename_map:
            df = df.rename(columns=rename_map)
        print("✅ File successfully loaded!")
        return df
    except Exception as e:
        print(f"❌ An error occurred while reading the file: {e}")
        return None

def filter_appropriate_rows(df: pd.DataFrame, target_casrn: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filters a DataFrame to find appropriate rows based on CAS number and name criteria.
    It also returns the rows that were rejected and the reason for rejection.

    Args:
        df (pd.DataFrame): The input DataFrame with chemical data.
        target_casrn (str): The target CAS number to match against.

    Returns:
        Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: A tuple containing two lists:
            - The first list contains dictionaries for appropriate rows.
            - The second list contains dictionaries for rejected rows, including a rejection reason.
    """
    appropriate_rows = []
    rejected_rows = []
    
    # Define the regex pattern for a CASRN-type string
    casrn_pattern = re.compile(r'\d{2,7}-\d{2}-\d')

    for index, row in df.iterrows():
        # Get values, handling potential non-string data by converting to string
        name = str(row.get("Name", "")).lower()
        cas_number = str(row.get("Cas Number", ""))
        row_dict = row.to_dict()

        # Condition 2: Check for "reaction mass" in the name. If it exists, the row is not appropriate.
        if "reaction mass" in name:
            row_dict['rejection_reason'] = 'Contains "reaction mass" in Name'
            rejected_rows.append(row_dict)
            continue

        # Condition 3: Check for a non-matching CASRN-type string in the name.
        # Find all CASRN-like strings in the name field.
        found_casrns_in_name = casrn_pattern.findall(name)
        # Check if any of the found CASRNs do not match the target.
        if any(cas != target_casrn for cas in found_casrns_in_name):
            row_dict['rejection_reason'] = 'Contains non-matching CASRN in Name'
            rejected_rows.append(row_dict)
            continue

        # Condition 1: If the Cas Number matches the target, the row IS appropriate.
        if cas_number == target_casrn:
            appropriate_rows.append(row_dict)
        else:
            # If not accepted, it's rejected for not matching the target CASRN.
            row_dict['rejection_reason'] = 'CAS Number does not match target'
            rejected_rows.append(row_dict)
            
    return appropriate_rows, rejected_rows

def process_substance_pages(appropriate_data: List[Dict[str, Any]], driver: webdriver.Chrome) -> List[Dict[str, Any]]:
    """
    Navigates through substance pages, scrapes detail links from the C&L Inventory,
    and returns a list of consolidated data.

    Args:
        appropriate_data (List[Dict[str, Any]]): A list of dictionaries representing appropriate rows.
        driver (webdriver.Chrome): The active Selenium WebDriver instance.
        
    Returns:
        List[Dict[str, Any]]: A list of dictionaries, where each dictionary contains the original
                              info plus the scraped 'number_of_notifiers' and 'details_page_url'.
    """
    if not appropriate_data:
        print("\nNo appropriate pages to process for this CASRN.")
        return []

    all_scraped_details = []

    # Loop through each appropriate row
    for i, item in enumerate(appropriate_data):
        url = item.get("Substance Information Page")
        name = item.get("Name")

        # Validate the URL before trying to navigate
        if not url or not isinstance(url, str) or not url.startswith('http'):
            print(f"--> Skipping entry {i+1} ('{name}') due to invalid or missing URL: {url}")
            continue

        print(f"\n({i+1}/{len(appropriate_data)}) Processing Infocard page for: {name}")
        print(f"    URL: {url}")
        
        driver.get(url)
        
        try:
            cookie_accept_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept all cookies')]"))
            )
            print("    -> Found cookie banner. Clicking 'Accept all cookies'.")
            cookie_accept_button.click()
        except TimeoutException:
            print("    -> No cookie banner found, or it was already accepted. Continuing.")

        print("    -> Searching for 'C&L Inventory' link...")
        try:
            cl_inventory_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[normalize-space() = 'Notified C&L']"))
            )
            print("    -> Found link. Navigating to C&L Inventory page.")
            driver.execute_script("arguments[0].click();", cl_inventory_link)

            # Scrape the C&L Inventory Page
            print("    -> Now on C&L Inventory page. Scraping details table...")
            
            try:
                rows = WebDriverWait(driver, 15).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table.CLPtable > tbody > tr"))
                )
                print(f"    -> Found {len(rows)} rows in the table.")

                for row_element in rows:
                    try:
                        notifier_cell = row_element.find_element(By.CSS_SELECTOR, "td:nth-child(10)")
                        num_notifiers = int(notifier_cell.text.strip())
                    except (NoSuchElementException, ValueError):
                        num_notifiers = 0 
                    
                    try:
                        details_link_element = row_element.find_element(By.CSS_SELECTOR, "td:nth-child(12) a.details")
                        details_url = details_link_element.get_attribute('href')
                    except NoSuchElementException:
                        details_url = None

                    if details_url: 
                        # Combine original item data with the new scraped data
                        combined_info = item.copy()
                        combined_info['number_of_notifiers'] = num_notifiers
                        combined_info['details_page_url'] = details_url
                        all_scraped_details.append(combined_info)

                if not any(d['details_page_url'] for d in all_scraped_details):
                        combined_info = item.copy()
                        combined_info['number_of_notifiers'] = None
                        combined_info['details_page_url'] = None
                        all_scraped_details.append(combined_info)
                   
                        print("\n    --- No 'View details' links found on this page. ---")

            except TimeoutException:
                print("    -> Could not find the details table rows on the C&L Inventory page within 15 seconds.")

        except TimeoutException:
            print("    -> Could not find the 'Notified C&L' link on the Infocard page.")
            
    return all_scraped_details


# --- Main execution block ---
if __name__ == '__main__':
    # Define the base directory where your CSV files are stored.
    csv_directory = config.ECHA_PAGES

    
    mastercas = pd.read_parquet(config.MASTER_CAS_LIST)
    casrns_to_test = mastercas.CASRN.tolist()

    dlst = os.listdir(csv_directory)
    havelst = []
    for fn in dlst:
        try:
            casrns_to_test.remove(fn.split('_')[1]) # gets the casrn part
        except:
            pass # ignore other files with different name structure
    

    # --- 1. Initialize the WebDriver ONCE for the entire session ---
    print("Initializing browser for the entire session...")
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    input('testing beginning -> press enter >> ')

    try:
        # --- 2. Loop through each test case ---
        for test_casrn in casrns_to_test:
            print(f"\n{'='*20} Processing Test Case for CASRN: {test_casrn} {'='*20}")

            # Derive the filename from the target CASRN
            filename = f"{test_casrn}_search_res.csv"
            csv_file_path = os.path.join(csv_directory, filename)

            inventory_links_df = load_chem_links_from_local_csv(csv_file_path)

            if inventory_links_df is not None:
                print(f"\nFiltering for target CASRN: {test_casrn}")
                appropriate_data, rejected_data = filter_appropriate_rows(inventory_links_df, test_casrn)

                print(f"\n--- Found {len(appropriate_data)} Appropriate Rows ---")
                # ... [Display logic for appropriate/rejected rows remains the same] ...
                
                # Process the pages and get back all the scraped details
                collected_details = process_substance_pages(appropriate_data, driver)
                
                # --- NEW: Save the collected data to a Parquet file ---
                if collected_details:
                    final_df = pd.DataFrame(collected_details)
                    
                    # Sanitize the name from the first appropriate entry for use in a filename
                    first_name = appropriate_data[0].get("Name", "unknown").strip()
                    sanitized_name = re.sub(r'[\\/*?:"<>|]', "", first_name).replace(' ', '_').lower()
                    
                    # Construct filename and full path
                    save_filename = f'details_{test_casrn}_{sanitized_name}.parquet'
                    save_path = os.path.join(csv_directory, save_filename)
                    
                    # Save the DataFrame to a Parquet file
                    final_df.to_parquet(save_path, index=False)
                    print(f"\n✅ Successfully saved {len(final_df)} detail links to:")
                    print(f"   {save_path}")
                else:
                    print("\nNo detail links were scraped, so no file was saved.")

            print(f"\n--- Finished processing CASRN: {test_casrn} ---")

    finally:
        # --- 3. Clean Up ONCE at the very end ---
        print("\nAll test cases processed. Closing the browser.")
        driver.quit()


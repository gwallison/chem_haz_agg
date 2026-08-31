# -*- coding: utf-8 -*-
"""
Created on Sun Jan 25 14:40:12 2026

@author: Gary
"""

import argparse
import os
import sys
import time
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup

# Add the project root to the Python path to resolve the 'config' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config

# --- Configuration ---
BASE_URL = "https://echa.europa.eu/information-on-chemicals"
SAVE_DIRECTORY = config.ECHA_PAGES
# OUT_DF = os.path.join(SAVE_DIRECTORY,'CL_Inventory_page_links.parquet')
# DEBUG_DIRECTORY = "debug_output"
DELAY_BETWEEN_REQUESTS = 3

# On the results page, exactly one of these ends up visible once ECHA's search
# resolves: the CSV export button (results found) or this banner (confirmed
# zero results). Racing both means we don't have to sit through a full
# timeout just to learn a CASRN genuinely has no ECHA registrations.
CSV_BUTTON_ID = "_disssimplesearch_WAR_disssearchportlet_exportButtonCSV"
NO_RESULTS_MSG_ID = "_disssimplesearch_WAR_disssearchportlet_rmlSearchResultVOsSearchContainerEmptyResultsMessage"

def initialize_driver():
    """Initializes and returns a Selenium WebDriver."""
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# def get_output_df():
#     return pd.read_parquet(OUT_DF)

# def save_output_df(df):
#     df.to_parquet(OUT_DF)

def is_timeout_placeholder_csv(csv_path):
    """
    True if this search_res.csv is the empty-DataFrame fallback written by
    click_and_download_csv() when the CSV download button couldn't be found in
    time (a network/UI hiccup, not necessarily a real "no results" from ECHA).
    Real ECHA exports always have a title row, a blank/meta row, and a header
    row before any data, so they're never fewer than 3 lines.
    """
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        return line_count < 3
    except OSError:
        return False

def _no_results_message_visible(driver):
    """
    True if ECHA's "No results were found." banner is currently shown.
    The results page always contains this element; ECHA toggles a "hide"
    class on it (and the opposite on the results table) once the search
    resolves, so its absence just means the search hasn't resolved yet.
    """
    try:
        el = driver.find_element(By.ID, NO_RESULTS_MSG_ID)
    except NoSuchElementException:
        return False
    classes = (el.get_attribute("class") or "").split()
    return "hide" not in classes

def write_confirmed_no_results_csv(cas):
    """
    Writes a zero-row placeholder matching the real ECHA export's header
    format for a CASRN ECHA has confirmed has no registrations. Using the
    real header (instead of an empty pd.DataFrame) means it parses cleanly
    downstream and doesn't get flagged by is_timeout_placeholder_csv as a
    candidate to retry -- ECHA already gave us a definitive answer.
    """
    dfn = os.path.join(SAVE_DIRECTORY, f'{cas}_search_res.csv')
    content = (
        "﻿Registered Substances\n"
        f"Export date: {{0}} {time.strftime('%m/%d/%Y %H:%M:%S')}\n"
        "\n"
        '"Name"\t"EC / List Number"\t"Cas Number"\t"Substance Information Page"\t'
        '"exported-column-briefProfileLink"\t"exported-column-obligationsLink"\t\n'
    )
    with open(dfn, 'w', encoding='utf-8') as f:
        f.write(content)

def has_been_crawled(cas_number, save_dir):
    """Checks if any page for a given CAS number has already been saved."""
    if not os.path.exists(save_dir):
        return False
    pattern = re.compile(f"^{re.escape(cas_number)}_\\d+_\\d+\\.html$")
    for filename in os.listdir(save_dir):
        if pattern.match(filename):
            return True
    return False

def save_page_source(full_filename, page_source, save_dir):
    """Saves the page source to a file."""
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, full_filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(page_source)
    print(f"  - Saved page to {file_path}")

# def save_debug_info(driver, cas_number):
#     """Saves a screenshot and the HTML source for debugging purposes."""
#     os.makedirs(DEBUG_DIRECTORY, exist_ok=True)
#     screenshot_path = os.path.join(DEBUG_DIRECTORY, f"{cas_number}_error.png")
#     html_path = os.path.join(DEBUG_DIRECTORY, f"{cas_number}_error.html")
#     try:
#         driver.save_screenshot(screenshot_path)
#         with open(html_path, "w", encoding="utf-8") as f:
#             f.write(driver.page_source)
#         print(f"  - DEBUG: Saved screenshot to {screenshot_path}")
#         print(f"  - DEBUG: Saved HTML source to {html_path}")
#     except Exception as e:
#         print(f"  - DEBUG: Could not save debug info: {e}")

def click_and_download_csv(driver, cas,
                           download_path=r"C:\Users\Gary\Downloads"):
    """
    Finds and clicks the CSV download button on the current page and waits for the download.

    Args:
        driver: The Selenium WebDriver instance, already navigated to the correct page.
        download_path (str): The absolute path to the folder where the CSV will be saved.
    """
    import shutil
    try:
        # --- 1. Locate and click the CSV download button ---
        # search_and_save_details already confirmed this is clickable before calling us.
        wait = WebDriverWait(driver, 20)
        csv_button = wait.until(EC.element_to_be_clickable((By.ID, CSV_BUTTON_ID)))

        # Get a list of files in the download directory *before* clicking
        files_before = os.listdir(download_path)

        # print("CSV button found. Clicking to download...")
        csv_button.click()

        # --- 2. Wait for the new file to appear ---
        # print("Waiting for download to start...")
        time.sleep(2) # Give a brief moment for the download to initiate

        # Poll the directory until a new file appears or timeout occurs
        wait_time = 0
        while wait_time < 30: # Max wait 30 seconds
            files_after = os.listdir(download_path)
            new_files = [f for f in files_after if f not in files_before and (f.endswith('.csv') or f.endswith('.crdownload'))]
            if new_files:
                print(f"New file '{new_files[0]}' appeared in download directory.")
                # Optional: Wait for .crdownload file to be renamed
                while any(f.endswith('.crdownload') for f in os.listdir(download_path)):
                    time.sleep(1)
                    print("...finishing download...")
                sfn = os.path.join(download_path,new_files[0])
                dfn = os.path.join(SAVE_DIRECTORY,f'{cas}_search_res.csv')
                shutil.move(sfn,dfn)
                # print("Download completed.")
                return True
            time.sleep(1)
            wait_time += 1
        
        print("Error: Download did not complete within 30 seconds.")
        return False

    except TimeoutException:
        print("Error: Could not find the CSV download button within 20 seconds.")
        print("Saving an empty dataframe.")
        dfn = os.path.join(SAVE_DIRECTORY,f'{cas}_search_res.csv')
        tmp = pd.DataFrame()
        tmp.to_csv(dfn)
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False

def search_and_save_details(driver, cas_number):
    """
    This function assumes the driver is on the main search page and ready.
    It performs a search and navigates to the C&L Inventory page.
    """
    try:
        # --- Perform Search ---
        driver.get(BASE_URL)

        search_box = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "autocompleteKeywordInput")))
        search_box.clear()
        search_box.send_keys(cas_number)
        driver.find_element(By.ID, "_disssimplesearchhomepage_WAR_disssearchportlet_searchButton").click()

        # input('waiting on user input >> ')
        # --- Race results-found against confirmed-no-results, whichever resolves first ---
        WebDriverWait(driver, 20).until(
            EC.any_of(
                EC.element_to_be_clickable((By.ID, CSV_BUTTON_ID)),
                _no_results_message_visible,
            )
        )

        if _no_results_message_visible(driver):
            print(f"  - ECHA confirms no results for {cas_number}.")
            write_confirmed_no_results_csv(cas_number)
            return True

        click_and_download_csv(driver,cas_number)

    except Exception as e:
        print(f"  - An unexpected error occurred for CAS {cas_number}: {e}")
        # save_debug_info(driver, cas_number)
        return False

def main(cas_numbers):
    """Main function to orchestrate the web scraping process."""
    driver = initialize_driver()
    driver.get(BASE_URL)
    input('Initial set up.  Waiting for you > ')
    # casout = []
    # urlout = []
    try:
        for i,cas in enumerate(cas_numbers):
            print(f"  - working on {cas}: {i} of {len(cas_numbers)}.")
            _ = search_and_save_details(driver, cas)

            print(f"  - Finished processing {cas}.")
            time.sleep(DELAY_BETWEEN_REQUESTS)

    finally:
        driver.quit()
        print("\nScraping finished.")

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--retry-timeouts', action='store_true',
        help="Re-attempt CASRNs whose search_res.csv is the empty-dataframe placeholder "
             "written when the CSV download timed out, instead of skipping them as "
             "already-crawled. A successful re-download overwrites the placeholder."
    )
    args = parser.parse_args()

    mastercas = pd.read_parquet(config.MASTER_CAS_LIST)
    cas_list_to_process = mastercas.CASRN.tolist()

    dlst = os.listdir(SAVE_DIRECTORY)
    retry_count = 0
    for fn in dlst:
        cas = fn.split('_')[0]
        if args.retry_timeouts and fn.endswith('_search_res.csv'):
            full_path = os.path.join(SAVE_DIRECTORY, fn)
            if is_timeout_placeholder_csv(full_path):
                retry_count += 1
                continue  # leave it in cas_list_to_process so it gets re-attempted
        try:
            cas_list_to_process.remove(cas)
        except ValueError:
            pass

    if args.retry_timeouts:
        print(f"--retry-timeouts: {retry_count} timed-out placeholder CSVs will be re-attempted.")

    main(cas_list_to_process)

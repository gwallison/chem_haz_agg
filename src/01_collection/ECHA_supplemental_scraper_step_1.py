import os
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

# --- Configuration ---
BASE_URL = "https://echa.europa.eu/information-on-chemicals"
SAVE_DIRECTORY = "echa_pages"
OUT_DF = os.path.join(SAVE_DIRECTORY,'CL_Inventory_page_links.parquet')
DEBUG_DIRECTORY = "debug_output"
DELAY_BETWEEN_REQUESTS = 3

def initialize_driver():
    """Initializes and returns a Selenium WebDriver."""
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def get_output_df():
    return pd.read_parquet(OUT_DF)

def save_output_df(df):
    df.to_parquet(OUT_DF)

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

def save_debug_info(driver, cas_number):
    """Saves a screenshot and the HTML source for debugging purposes."""
    os.makedirs(DEBUG_DIRECTORY, exist_ok=True)
    screenshot_path = os.path.join(DEBUG_DIRECTORY, f"{cas_number}_error.png")
    html_path = os.path.join(DEBUG_DIRECTORY, f"{cas_number}_error.html")
    try:
        driver.save_screenshot(screenshot_path)
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print(f"  - DEBUG: Saved screenshot to {screenshot_path}")
        print(f"  - DEBUG: Saved HTML source to {html_path}")
    except Exception as e:
        print(f"  - DEBUG: Could not save debug info: {e}")

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
        csv_button_id = "_disssimplesearch_WAR_disssearchportlet_exportButtonCSV"
        # print(f"Waiting for CSV button with ID: {csv_button_id}")

        wait = WebDriverWait(driver, 10)
        csv_button = wait.until(EC.element_to_be_clickable((By.ID, csv_button_id)))

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
        print("Error: Could not find the CSV download button within 10 seconds.")
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
        # --- Navigate from search results to substance page ---
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody.table-data")))
        click_and_download_csv(driver,cas_number)

    except Exception as e:
        print(f"  - An unexpected error occurred for CAS {cas_number}: {e}")
        save_debug_info(driver, cas_number)
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
    
    fn = r"C:\MyDocs\integrated\chem_profiles\code\data\master_cas_list.parquet"
    mastercas = pd.read_parquet(fn)
    cas_list_to_process = mastercas.CASRN.tolist()

    dlst = os.listdir(SAVE_DIRECTORY)
    for fn in dlst:
        try:
            cas_list_to_process.remove(fn.split('_')[0])
        except:
            pass
    main(cas_list_to_process)

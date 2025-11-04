import time
import pandas as pd
from io import StringIO
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

# Import webdriver_manager and Service
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- Selectors ---
ECL_COOKIE_HOST_SELECTOR = (By.TAG_NAME, "ecl-cookie-consent-banner")
COOKIE_ACCEPT_SELECTOR = (By.CSS_SELECTOR, "button.ecl-button.ecl-button--primary")
MAIN_CONTENT_HOST_SELECTOR = (By.TAG_NAME, "cnldas-self-classifications-app")
TABS_SELECTOR = (By.CSS_SELECTOR, "div.das-lib-tabs_header-item")
TABLE_CONTAINER_SELECTOR = (By.CSS_SELECTOR, "section.cnl-classification")
TABLE_SELECTOR = (By.TAG_NAME, "table")
NEXT_BUTTON_SELECTOR = (By.CSS_SELECTOR, "div.cnl-nav-secondary a:last-of-type")
NO_RESULTS_SELECTOR = (By.CSS_SELECTOR, "div.cnl-no-results h3")
TAB_NOT_CLASSIFIED_SELECTOR = (By.CSS_SELECTOR, "div.cnl-muted")

# Selectors for the composite wait (NOW REMOVED)
# CONTENT_HEADER_SELECTOR = (By.CSS_SELECTOR, "section.cnl-title-details h3")
# CONTENT_PERCENTAGE_SELECTOR = (By.CSS_SELECTOR, "section.cnl-title-details span.cnl-notif-percentage")
# PANE_CONTENT_SELECTOR = (By.CSS_SELECTOR, "section.cnl-classification app-simple-table, section.cnl-classification div.cnl-muted")
# ---------------------

def get_shadow_root(driver, host_element):
    """
    Returns the shadow root of a given host element.
    """
    return driver.execute_script('return arguments[0].shadowRoot', host_element)

def scrape_echa_substance(driver, url, casrn, ec_number):
    """
    Scrapes all self-classification tables for a single substance URL
    using a pre-initialized driver.
    """
    
    all_dfs = [] 
    page_num = 1
    
    try:
        print(f"  Opening URL: {url}")
        driver.get(url)

        # --- Step 1: Access Main Content's Shadow DOM ---
        main_content_host = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(MAIN_CONTENT_HOST_SELECTOR)
        )
        main_shadow_root = get_shadow_root(driver, main_content_host)

        # --- Step 2: Check for "No associated classifications" (Case 1) ---
        try:
            no_results_header = WebDriverWait(driver, 2).until(
                lambda d: main_shadow_root.find_element(NO_RESULTS_SELECTOR[0], NO_RESULTS_SELECTOR[1])
            )
            if "No associated classifications" in no_results_header.text:
                print("  Found 'No associated classifications' message.")
                return 'NO_ASSOCIATED_CLASSIFICATIONS' 
        except (TimeoutException, NoSuchElementException):
            print("  No 'Page Level No Data' message found, proceeding to scrape tabs.")
            pass 
        # -----------------------------------------------------------------

        # --- Step 3: Pagination Loop ---
        while True:
            print(f"  Scraping Tab Page {page_num}...")
            
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: main_shadow_root.find_element(TABS_SELECTOR[0], TABS_SELECTOR[1])
                )
            except TimeoutException:
                print("  No tabs found on this page.")
                break
                
            tabs = main_shadow_root.find_elements(TABS_SELECTOR[0], TABS_SELECTOR[1])
            num_tabs = len(tabs)
            
            if not tabs:
                print("  No tabs found, ending pagination.")
                break
            first_tab_on_page = tabs[0]

            # 4. Loop through *visible* tabs
            for i in range(num_tabs):
                tab_info = {}
                try:
                    tabs = main_shadow_root.find_elements(TABS_SELECTOR[0], TABS_SELECTOR[1])
                    tab = tabs[i]

                    # 5. Get tab info
                    try:
                        tab_info['type'] = tab.find_element(By.CSS_SELECTOR, "div.das-registration-type").text
                        tab_info['percentage'] = tab.find_element(By.CSS_SELECTOR, "div.das-percentage").text
                        tab_info['order'] = tab.find_element(By.CSS_SELECTOR, "div.das-tab-order").text
                        tab_info['status'] = tab.find_element(By.CSS_SELECTOR, "div.das-submission-status").text
                    except NoSuchElementException:
                        print("    Warning: Tab is missing standard info. Using fallback.")
                        tab_info['full_text'] = tab.text.replace('\n', ' | ')
                        tab_info['type'] = tab_info.get('full_text', 'Unknown')
                        tab_info['percentage'] = None

                    # 6. Click the tab
                    tab.click()

                    # --- [NEW] Hard-coded wait ---
                    print("    Waiting 2 seconds for tab content to load...")
                    time.sleep(2)
                    # --------------------------------

                    # 7. Now that content is (hopefully) loaded, get the classification container
                    table_container_pane = main_shadow_root.find_element(TABLE_CONTAINER_SELECTOR[0], TABLE_CONTAINER_SELECTOR[1])

                    # 8. Find all tables
                    tables = table_container_pane.find_elements(TABLE_SELECTOR[0], TABLE_SELECTOR[1])
                    
                    if tables:
                        print(f"    Found {len(tables)} tables on this tab.")
                        for table_index, table in enumerate(tables):
                            table_html = table.get_attribute('outerHTML')
                            df_list = pd.read_html(StringIO(table_html))
                            
                            if df_list:
                                df = df_list[0]
                                df['tab_table_index'] = table_index
                                df['scrape_status'] = 'Success'
                                for key, value in tab_info.items():
                                    df[f'tab_{key}'] = value
                                all_dfs.append(df)
                    else:
                        # No tables found, check if it's a "Not classified" tab
                        try:
                            not_classified_div = table_container_pane.find_element(TAB_NOT_CLASSIFIED_SELECTOR[0], TAB_NOT_CLASSIFIED_SELECTOR[1])
                            if "Not classified" in not_classified_div.text:
                                print("    Tab marked 'Not classified'. Logging row.")
                                no_data_payload = {
                                    'scrape_status': 'Not classified',
                                    **{f'tab_{k}': v for k, v in tab_info.items()}
                                }
                                all_dfs.append(pd.DataFrame([no_data_payload]))
                        except NoSuchElementException:
                            print("    Tab section found, but no tables or 'Not classified' message.")
                            pass
                    
                except TimeoutException:
                    print(f"    Content for tab '{tab_info.get('type')}' did not load in time. Skipping tab.")
                    continue
                except StaleElementReferenceException as e:
                    print(f"    Stale element error on tab {i}. Skipping tab. Error: {e}")
                    continue
            
            # --- Step 5: Pagination Logic ---
            try:
                next_button_anchor = main_shadow_root.find_element(NEXT_BUTTON_SELECTOR[0], NEXT_BUTTON_SELECTOR[1])
                
                if "cnl-disabled" in next_button_anchor.get_attribute("class"):
                    print("  'Next' button is disabled. End of tabs for this substance.")
                    break 
                else:
                    print("  Clicking 'Next' button...")
                    next_button_anchor.click()
                    WebDriverWait(driver, 10).until(
                        EC.staleness_of(first_tab_on_page)
                    )
                    page_num += 1

            except NoSuchElementException:
                print("  No 'Next' button found. End of tabs for this substance.")
                break 

    except TimeoutException:
        print("  Error: Main page content did not load.")
        return None 
    except Exception as e:
        print(f"  An unexpected error occurred: {e}")
        return None 
    
    # --- Process and Return Data ---
    if not all_dfs:
        print("  Tabs found, but no data scraped (all tabs were empty).")
        return None

    print(f"  Processing {len(all_dfs)} scraped dataframes...")
    final_substance_df = pd.concat(all_dfs, ignore_index=True)
    
    final_substance_df['CASRN'] = casrn
    final_substance_df['ec_number'] = ec_number
    final_substance_df['source_url'] = url
    
    return final_substance_df

# --- Main script to run the loop (UNCHANGED) ---
if __name__ == "__main__":
    
    try:
        import config 
    except ImportError:
        print("Error: Could not import 'config' module.")
        exit()

    # Define paths
    links_path = Path(config.ECHA_SUBSTANCE_LINKS)
    output_dir = Path(config.INTERMED_DATA)
    output_path = output_dir / 'echa_self_classifications.parquet'
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # --- Load existing data for resuming ---
    print(f"Checking for existing data at: {output_path}")
    if output_path.exists():
        try:
            existing_df = pd.read_parquet(output_path)
            if 'CASRN' in existing_df.columns and 'ec_number' in existing_df.columns:
                processed_keys = set(zip(existing_df['CASRN'], existing_df['ec_number']))
                print(f"  Found {len(existing_df)} existing records.")
                print(f"  Resuming. {len(processed_keys)} (CAS, EC) pairs already processed.")
            else:
                print("  Existing file is missing 'CASRN' or 'ec_number'. Wiping and starting fresh.")
                existing_df = pd.DataFrame()
                processed_keys = set()
        except Exception as e:
            print(f"  Error reading existing parquet file: {e}. Starting fresh.")
            existing_df = pd.DataFrame()
            processed_keys = set()
    else:
        print("  No existing data file found. Starting fresh.")
        existing_df = pd.DataFrame()
        processed_keys = set()
    # ----------------------------------------------
    
    print(f"Loading substance links from: {links_path}")
    try:
        links_df = pd.read_parquet(links_path)
    except Exception as e:
        print(f"Error loading Parquet file: {e}")
        exit()
        
    total_substances = len(links_df)
    print(f"Found {total_substances} total substances to process.")
    
    # --- Initialize ONE driver ---
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    driver = None
    print("Setting up shared WebDriver...")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"CRITICAL Error setting up WebDriver: {e}")
        exit()
    
    # --- Handle cookies ONCE ---
    print("Opening base URL to handle cookies...")
    try:
        driver.get("https://chem.echa.europa.eu/")
        cookie_host = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(ECL_COOKIE_HOST_SELECTOR)
        )
        cookie_shadow_root = get_shadow_root(driver, cookie_host)
        cookie_button = WebDriverWait(driver, 5).until(
            lambda d: cookie_shadow_root.find_element(COOKIE_ACCEPT_SELECTOR[0], COOKIE_ACCEPT_SELECTOR[1])
        )
        cookie_button.click()
        print("Clicked 'Accept all cookies'.")
        time.sleep(1) 
    except TimeoutException:
        print("No cookie banner found. Continuing...")
    except Exception as e:
        print(f"Warning: Error handling cookie banner: {e}")
    # ------------------------------------

    try:
        for index, row in links_df.iterrows():
            
            print(f"\n--- Processing Substance {index + 1} of {total_substances} ---")
            
            try:
                casrn = row.get('CASRN')
                ec_num = row.get('ec_number')
                substance_id = row.get('substance_ID')

                if not substance_id:
                    print(f"  Skipping row {index} due to missing 'substance_ID'.")
                    continue
                
                key = (casrn, ec_num)
                print(f"  CAS: {casrn}, EC: {ec_num}")

                if key in processed_keys:
                    print("  Substance already processed. Skipping.")
                    continue
                
                url = f"https://chem.echa.europa.eu/{substance_id}/self-classified"
                
                substance_df_or_flag = scrape_echa_substance(driver, url, casrn, ec_num)
                
                substance_df = None
                
                if isinstance(substance_df_or_flag, pd.DataFrame):
                    print(f"  Successfully processed {len(substance_df_or_flag)} rows for {casrn}.")
                    substance_df = substance_df_or_flag
                
                elif substance_df_or_flag == 'NO_ASSOCIATED_CLASSIFICATIONS':
                    print(f"  No classification data found for {casrn}. Creating 'No Data' entry.")
                    substance_df = pd.DataFrame([{
                        'CASRN': casrn,
                        'ec_number': ec_num,
                        'source_url': url,
                        'scrape_status': 'No associated classifications'
                    }])
                
                elif substance_df_or_flag is None:
                    print(f"  Tabs found but no tables scraped for {casrn}. Creating 'Empty' entry.")
                    substance_df = pd.DataFrame([{
                        'CASRN': casrn,
                        'ec_number': ec_num,
                        'source_url': url,
                        'scrape_status': 'Tabs found but no data'
                    }])

                if substance_df is not None:
                    existing_df = pd.concat([existing_df, substance_df], ignore_index=True)
                    existing_df.to_parquet(output_path, index=False)
                    processed_keys.add(key)
                    print(f"  Saved {len(substance_df)} new row(s) to Parquet file.")
                else:
                    print(f"  No data frame produced for {casrn} (this shouldn't happen).")

            except Exception as e:
                print(f"  *** CRITICAL ERROR scraping substance_ID {row.get('substance_ID', 'N/A')}: {e} ***")
                print("  Continuing to next substance...")
            
            print("  Waiting 3 seconds...")
            time.sleep(3)
    
    finally:
        if driver:
            print("\n--- All processing finished. Closing shared WebDriver. ---")
            driver.quit()
    # -----------------------------------------------------------------
            
    print("\n--- Scraping complete. ---")
    if output_path.exists():
        try:
            final_df = pd.read_parquet(output_path)
            print(f"Final dataset has {len(final_df)} rows.")
            print(f"Data is saved at: {output_path}")
        except Exception as e:
            print(f"Error reading final parquet file: {e}")
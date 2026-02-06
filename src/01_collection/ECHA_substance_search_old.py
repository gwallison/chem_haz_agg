import time
import pandas as pd
from io import StringIO # [NEW] Import StringIO to fix pandas warning
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException

# Import webdriver_manager and Service
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
URL = 'https://chem.echa.europa.eu/100.000.002/self-classified'

# --- Selectors ---

# Host element for the EU cookie banner
ECL_COOKIE_HOST_SELECTOR = (By.TAG_NAME, "ecl-cookie-consent-banner")
# Button *inside* the cookie shadow DOM
COOKIE_ACCEPT_SELECTOR = (By.CSS_SELECTOR, "button.ecl-button.ecl-button--primary")

# Host element for the main page content
MAIN_CONTENT_HOST_SELECTOR = (By.TAG_NAME, "cnldas-self-classifications-app")

# --- Selectors *inside* the MAIN_CONTENT_HOST's shadow DOM ---
TABS_SELECTOR = (By.CSS_SELECTOR, "div.das-lib-tabs_header-item")
TABLE_CONTAINER_SELECTOR = (By.CSS_SELECTOR, "section.cnl-classification")
TABLE_SELECTOR = (By.TAG_NAME, "table")

# [UPDATED] Selector for the "Next" pagination button (must be CSS, not XPATH)
NEXT_BUTTON_SELECTOR = (By.CSS_SELECTOR, "div.cnl-nav-secondary a:last-of-type")

# ---------------------

def get_shadow_root(driver, host_element):
    """
    Returns the shadow root of a given host element.
    """
    return driver.execute_script('return arguments[0].shadowRoot', host_element)

def scrape_echa_page(url):
    """
    Scrapes all tables from all tabs on the ECHA self-classified page,
    handling tab pagination.
    """
    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--start-maximized')
    
    print("Setting up WebDriver...")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        print(f"Error setting up WebDriver: {e}")
        return []
    
    print(f"Opening URL: {url}")
    driver.get(url)

    # --- Step 1: Handle Cookie Banner (in its own Shadow DOM) ---
    try:
        print("Looking for cookie banner host...")
        cookie_host = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(ECL_COOKIE_HOST_SELECTOR)
        )
        print("Cookie banner host found. Accessing its shadow DOM.")
        
        cookie_shadow_root = get_shadow_root(driver, cookie_host)
        
        cookie_button = WebDriverWait(driver, 5).until(
            lambda d: cookie_shadow_root.find_element(COOKIE_ACCEPT_SELECTOR[0], COOKIE_ACCEPT_SELECTOR[1])
        )
        
        print("Clicking 'Accept all cookies'.")
        cookie_button.click()
        time.sleep(1) 
    except TimeoutException:
        print("No cookie banner found, or it timed out. Continuing...")
    except Exception as e:
        print(f"Error handling cookie banner: {e}")
    # -----------------------------------------------------------

    scraped_data = []
    
    try:
        # --- Step 2: Access Main Content's Shadow DOM ---
        print("Waiting for main page content host...")
        main_content_host = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(MAIN_CONTENT_HOST_SELECTOR)
        )
        print("Main content host found. Accessing its shadow DOM.")
        
        main_shadow_root = get_shadow_root(driver, main_content_host)
        
        # --- [NEW] Step 3: Pagination Loop ---
        page_num = 1
        while True:
            print(f"\n--- Scraping Tab Page {page_num} ---")
            
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: main_shadow_root.find_element(TABS_SELECTOR[0], TABS_SELECTOR[1])
                )
            except TimeoutException:
                print("No tabs found on this page. Exiting.")
                break
                
            tabs = main_shadow_root.find_elements(TABS_SELECTOR[0], TABS_SELECTOR[1])
            num_tabs = len(tabs)
            print(f"Found {num_tabs} visible tabs on this page.")
            
            if not tabs:
                print("No tabs found, ending pagination.")
                break
            first_tab_on_page = tabs[0]

            # 4. Loop through *visible* tabs by index
            for i in range(num_tabs):
                tab_info = {}
                try:
                    tabs = main_shadow_root.find_elements(TABS_SELECTOR[0], TABS_SELECTOR[1])
                    tab = tabs[i]

                    # 5. Get tab info
                    try:
                        tab_info['order'] = tab.find_element(By.CSS_SELECTOR, "div.das-tab-order").text
                        tab_info['type'] = tab.find_element(By.CSS_SELECTOR, "div.das-registration-type").text
                        tab_info['percentage'] = tab.find_element(By.CSS_SELECTOR, "div.das-percentage").text
                        tab_info['status'] = tab.find_element(By.CSS_SELECTOR, "div.das-submission-status").text
                    except NoSuchElementException:
                        tab_info['full_text'] = tab.text.replace('\n', ' | ')

                    print(f"--- Processing Tab {i+1} on Page {page_num}: {tab_info.get('type', tab_info.get('full_text', 'N/A'))} ---")

                    # 6. Click the tab
                    tab.click()

                    # 7. Wait for the table's container
                    table_container_pane = WebDriverWait(driver, 10).until(
                        lambda d: main_shadow_root.find_element(TABLE_CONTAINER_SELECTOR[0], TABLE_CONTAINER_SELECTOR[1])
                    )

                    # 8. Find all tables *within that container*
                    tables = table_container_pane.find_elements(TABLE_SELECTOR[0], TABLE_SELECTOR[1])
                    
                    if not tables:
                        print("Section found, but no tables within it.")
                        continue

                    print(f"Found {len(tables)} tables on this tab.")

                    # 9. Scrape each table
                    for table_index, table in enumerate(tables):
                        table_html = table.get_attribute('outerHTML')
                        
                        # [UPDATED] Use StringIO to fix pandas warning
                        df_list = pd.read_html(StringIO(table_html))
                        
                        if df_list:
                            df = df_list[0]
                            scraped_data.append({
                                'tab_info': tab_info,
                                'table_index': table_index,
                                'data': df
                            })
                            print(f"Scraped table {table_index} with shape {df.shape}")

                except TimeoutException:
                    print(f"No 'Classification' table section found on this tab.")
                    continue
                except StaleElementReferenceException as e:
                    print(f"Stale element error on tab {i}. Skipping. Error: {e}")
                    continue
            
            # --- Step 5: Pagination Logic ---
            try:
                # Find the "Next" button *inside the shadow root*
                next_button_anchor = main_shadow_root.find_element(NEXT_BUTTON_SELECTOR[0], NEXT_BUTTON_SELECTOR[1])
                
                # Check if it's disabled
                if "cnl-disabled" in next_button_anchor.get_attribute("class"):
                    print("\n'Next' button is disabled. End of all tabs.")
                    break # Exit the while True loop
                else:
                    # If it's enabled, click it and wait for the page to update
                    print("\nClicking 'Next' button...")
                    next_button_anchor.click()
                    # Wait for the old first tab to go stale
                    WebDriverWait(driver, 10).until(
                        EC.staleness_of(first_tab_on_page)
                    )
                    print("New page of tabs loaded.")
                    page_num += 1

            except NoSuchElementException:
                print("\nNo 'Next' button found. Assuming end of all tabs.")
                break # Exit the while True loop

    except TimeoutException:
        print("Error: Main page content (tabs) did not load, even after handling cookies.")
    
    finally:
        if 'driver' in locals() and driver:
            driver.quit()
        
    return scraped_data

# --- Run the scraper ---
if __name__ == "__main__":
    all_data = scrape_echa_page(URL)
    
    print(f"\n\n--- Total Scraped Data ---")
    print(f"Successfully scraped data from {len(all_data)} tables.")
    
    if all_data:
        print(f"Scraped a total of {len(all_data)} tables.")
        # Example: Print info from the first and last table scraped
        print("\nExample data from the first table:")
        print(f"Tab Info: {all_data[0]['tab_info']}")
        print(all_data[0]['data'].head())
        
        if len(all_data) > 1:
            print("\nExample data from the last table:")
            print(f"Tab Info: {all_data[-1]['tab_info']}")
            print(all_data[-1]['data'].head())
import time
import pandas as pd
from io import StringIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
URL = 'https://chem.echa.europa.eu/100.000.002/self-classified'

# Host element for the main page content
MAIN_CONTENT_HOST_SELECTOR = (By.TAG_NAME, "cnldas-self-classifications-app")

# --- Selectors *inside* the MAIN_CONTENT_HOST's shadow DOM ---
TABS_SELECTOR = (By.CSS_SELECTOR, "div.das-lib-tabs_header-item")
TABLE_CONTAINER_SELECTOR = (By.CSS_SELECTOR, "section.cnl-classification")
TABLE_SELECTOR = (By.TAG_NAME, "table")
NEXT_BUTTON_SELECTOR = (By.CSS_SELECTOR, "div.cnl-nav-secondary a:last-of-type")

def get_shadow_root(driver, host_element):
    return driver.execute_script('return arguments[0].shadowRoot', host_element)

def js_click(driver, element):
    """Clicks an element using JavaScript to bypass 'ElementClickIntercepted' errors."""
    driver.execute_script("arguments[0].click();", element)

def scrape_echa_page(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    
    print("Setting up WebDriver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    print(f"Opening URL: {url}")
    driver.get(url)

    # --- MANUAL STEP ---
    print("\n" + "!"*50)
    print("ACTION REQUIRED:")
    print("1. Handle cookie banner manually.")
    print("2. Navigate to the 'Self-Classified' section if not already there.")
    print("3. Press ENTER here to start.")
    print("!"*50 + "\n")
    input("Press Enter to start scraping...")

    scraped_data = []
    
    try:
        main_content_host = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(MAIN_CONTENT_HOST_SELECTOR)
        )
        main_shadow_root = get_shadow_root(driver, main_content_host)
        
        page_num = 1
        while True:
            print(f"\n--- Scraping Tab Page {page_num} ---")
            
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: main_shadow_root.find_element(TABS_SELECTOR[0], TABS_SELECTOR[1])
                )
            except TimeoutException:
                print("No tabs found. Ending.")
                break
                
            tabs = main_shadow_root.find_elements(TABS_SELECTOR[0], TABS_SELECTOR[1])
            num_tabs = len(tabs)
            first_tab_on_page = tabs[0]

            for i in range(num_tabs):
                try:
                    # Refresh tab list to avoid stale elements
                    tabs = main_shadow_root.find_elements(TABS_SELECTOR[0], TABS_SELECTOR[1])
                    tab = tabs[i]

                    # Extract basic info for logs
                    label = tab.text.split('\n')[0] if '\n' in tab.text else "Unknown Tab"
                    print(f"Processing Tab {i+1}/{num_tabs}: {label}")

                    # USE JS CLICK TO AVOID INTERCEPTION
                    js_click(driver, tab)
                    time.sleep(1.5) # Give the table a moment to load

                    # Locate tables
                    container = main_shadow_root.find_element(TABLE_CONTAINER_SELECTOR[0], TABLE_CONTAINER_SELECTOR[1])
                    tables = container.find_elements(TABLE_SELECTOR[0], TABLE_SELECTOR[1])
                    
                    for idx, table in enumerate(tables):
                        html = table.get_attribute('outerHTML')
                        df = pd.read_html(StringIO(html))[0]
                        scraped_data.append({'page': page_num, 'tab': i, 'table': idx, 'data': df})
                        print(f"   Scraped table {idx} ({len(df)} rows)")

                except Exception as e:
                    print(f"   Error on tab {i}: {str(e)[:100]}")
                    continue
            
            # --- PAGINATION ---
            try:
                next_btn = main_shadow_root.find_element(NEXT_BUTTON_SELECTOR[0], NEXT_BUTTON_SELECTOR[1])
                if "cnl-disabled" in next_btn.get_attribute("class"):
                    print("Reached final page.")
                    break
                
                print("Moving to next page of tabs...")
                js_click(driver, next_btn) # USE JS CLICK HERE TOO
                
                WebDriverWait(driver, 10).until(EC.staleness_of(first_tab_on_page))
                page_num += 1
                time.sleep(1)
            except NoSuchElementException:
                break

    finally:
        print(f"\nScraping finished. Total records: {len(scraped_data)}")
        # driver.quit() # Keeping open for your review

    return scraped_data

if __name__ == "__main__":
    all_data = scrape_echa_page(URL)
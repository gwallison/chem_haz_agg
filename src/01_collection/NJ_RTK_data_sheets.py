import time
import pandas as pd
import os
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import config

def scrape_nj_hazardous_substances():
    url = "https://web.doh.nj.gov/rtkhsfs/factsheets.aspx?lan=english"
    
    # 1. Setup Selenium Options
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment to run without a window
    
    # 2. Initialize Driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get(url)
        print("Page loaded. Clicking 'Display All'...")
        
        # 3. Locate and click "Display All"
        # The ID in your HTML snippet is ContentPlaceHolder1_DisplayAll
        display_all_link = driver.find_element(By.ID, "ContentPlaceHolder1_DisplayAll")
        display_all_link.click()
        
        # 4. Wait for the table to refresh (PostBack takes a moment)
        time.sleep(5) 
        
        # 5. Pass the rendered HTML to BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 6. Find the table inside PanelRegular
        # Based on the HTML provided, the table is inside a div with ID 'ContentPlaceHolder1_PanelRegular'
        panel = soup.find(id="ContentPlaceHolder1_PanelRegular")
        table = panel.find('table')
        
        rows = []
        # Skip the header row (index 0)
        for tr in table.find_all('tr')[1:]:
            cols = tr.find_all('td')
            if len(cols) < 3:
                continue
                
            # Extract Substance No and the URL
            substance_link_tag = cols[0].find('a')
            substance_no = substance_link_tag.text.strip() if substance_link_tag else cols[0].text.strip()
            substance_url = substance_link_tag['href'] if substance_link_tag else None
            
            # Extract other fields
            chemical_name = cols[1].text.strip()
            cas_no = cols[2].text.strip()
            
            # Extract Spanish language link if it exists
            other_lang_tag = cols[3].find('a')
            other_lang_url = other_lang_tag['href'] if (other_lang_tag and 'href' in other_lang_tag.attrs) else None

            rows.append({
                "RTK_Substance_No": substance_no,
                "Substance_URL": substance_url,
                "Chemical_Name": chemical_name,
                "CASRN": cas_no,
                "Spanish_URL": other_lang_url
            })
            
        # 7. Create DataFrame
        df = pd.DataFrame(rows)
        return df

    finally:
        driver.quit()

# Run the scraper
if __name__ == "__main__":
    df_chemicals = scrape_nj_hazardous_substances()
    print(f"Successfully scraped {len(df_chemicals)} substances.")

    # Save to parquet
    df_chemicals.to_parquet(config.NJ_RTK_DATASHEET_PATH)
    print(f'Saved to {config.NJ_RTK_DATASHEET_PATH}')
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import sys

# Add the project root to the Python path to resolve the 'config' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config
import re


def scrape_niosh_cas_index(source_path, is_url=True):
    # 1. Fetch the HTML content
    if is_url:
        # NOTE: cdc.gov's Akamai WAF returns a 403 to plain `requests` traffic
        # (confirmed even with full browser headers), but allows a real browser.
        # Selenium is required here, not just a nicer User-Agent.
        options = Options()
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        try:
            driver.get(source_path)
            html_content = driver.page_source
        finally:
            driver.quit()
    else:
        with open(source_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

    # 2. Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 3. Locate the table
    table = soup.find('table')
    
    rows_list = []
    
    # 4. Iterate through table rows, skipping the header
    for tr in table.find_all('tr')[1:]:
        cols = tr.find_all('td')
        if len(cols) >= 2:
            raw_cas = cols[0].get_text(strip=True)
            
            # Extract Chemical Name and its link
            name_tag = cols[1].find('a')
            chemical_name = name_tag.get_text(strip=True) if name_tag else cols[1].get_text(strip=True)
            
            # --- TWEAK: Handle Parentheticals in CAS Numbers ---
            # Search for anything inside parentheses
            match = re.search(r'(.*)\s(\(.*\))', raw_cas)
            if match:
                cas_no = match.group(1).strip()  # The pure CASRN
                extra_info = match.group(2).strip()  # The (BPN) part
                chemical_name = f"{chemical_name} {extra_info}"
            else:
                cas_no = raw_cas

            # 5. Construct absolute URL
            link = ""
            if name_tag and name_tag.get('href'):
                link = name_tag['href']
                if link.startswith('/'):
                    link = f"https://www.cdc.gov{link}"
                elif not link.startswith('http'):
                    link = f"https://www.cdc.gov/niosh/npg/{link}"

            rows_list.append({
                "CASRN": cas_no,
                "Chemical_Name": chemical_name,
                "Link": link
            })

    # 6. Create DataFrame
    df = pd.DataFrame(rows_list)
    return df

# Example Usage:
# df = scrape_niosh_cas_index("https://www.cdc.gov/niosh/npg/npgdcas.html")
if __name__ == '__main__':
    
    df = scrape_niosh_cas_index("https://www.cdc.gov/niosh/npg/npgdcas.html")
    print(df.head())
    df.to_parquet(config.NIOSH_POCKET_PATH)
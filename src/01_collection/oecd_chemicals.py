# -*- coding: utf-8 -*-
"""
Created on Wed Dec 31 13:42:38 2025

@author: Gary
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import urljoin
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config

def scrape_oecd_chemicals():
    url = "https://hpvchemicals.oecd.org/ui/AllChemicals.aspx"
    # The base URL needs to handle the relative path './'
    base_url = "https://hpvchemicals.oecd.org/ui/"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Target rows that look like the snippet provided
    # These tables are often generated as a 'GridView' in ASP.NET
    rows = soup.find_all('tr')
    
    extracted_data = []

    for row in rows:
        cells = row.find_all('td')
        
        # We need at least the CASRN and Name columns
        if len(cells) >= 2:
            # Column 0: CASRN (contained in an <a> tag)
            cas_cell = cells[0]
            cas_link_tag = cas_cell.find('a')
            
            # Column 1: Chemical Name (also contained in an <a> tag)
            name_cell = cells[1]
            name_link_tag = name_cell.find('a')
            
            if cas_link_tag and name_link_tag:
                casrn = cas_link_tag.get_text(strip=True)
                chem_name = name_link_tag.get_text(strip=True)
                
                # Extract the href from the name link
                relative_href = name_link_tag.get('href', '')
                # Clean up the './' if present
                clean_href = relative_href.lstrip('./')
                full_link = base_url + clean_href
                
                extracted_data.append({
                    "CASRN": casrn,
                    "Chemical_Name": chem_name,
                    "Link": full_link
                })

    # Convert to DataFrame
    df = pd.DataFrame(extracted_data)
    
    # Filter out potential header remnants or empty strings
    df = df[df['CASRN'].str.contains(r'\d', na=False)] 
    
    return df

def scrape_oecd_full_details(detail_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    base_url = "https://hpvchemicals.oecd.org/ui/"

    # 1. Fetch the main shell page to find sub-page iframes
    try:
        res = requests.get(detail_url, headers=headers, timeout=15)
        shell_soup = BeautifulSoup(res.text, 'html.parser')
    except Exception as e:
        print(f"Error accessing shell page: {e}")
        return None

    # Identify the two sub-page URLs
    iframe1 = shell_soup.find('iframe', id=lambda x: x and 'Frm_Sids' in x)
    iframe2 = shell_soup.find('iframe', src=re.compile(r'SidsOrganigrame\.aspx'))

    results = {}

    # --- Process Iframe 1 (Identity & Available Info) ---
    if iframe1:
        u1 = urljoin(detail_url, iframe1['src'])
        try:
            soup1 = BeautifulSoup(requests.get(u1, headers=headers).text, 'html.parser')
            
            def get_val1(label):
                el = soup1.find(string=re.compile(label, re.I))
                if el:
                    td = el.find_parent('td')
                    if td and td.find_next_sibling('td'):
                        return td.find_next_sibling('td').get_text(strip=True)
                return None

            results['HPV'] = get_val1("HPV")
            results['Recognized Low Hazard'] = get_val1("Recognized Low hazard")
        except:
            pass

    # --- Process Iframe 2 (SIDS Organigrame & PDFs) ---
    if iframe2:
        u2 = urljoin(detail_url, iframe2['src'])
        try:
            soup2 = BeautifulSoup(requests.get(u2, headers=headers).text, 'html.parser')

            def get_val2(label):
                el = soup2.find(string=re.compile(label, re.I))
                if el:
                    td = el.find_parent('td')
                    if td and td.find_next_sibling('td'):
                        return td.find_next_sibling('td').get_text(strip=True)
                return None

            results['Current Status'] = get_val2("Current Status")
            
            # Extract PDF details as separate lists
            pdf_names = []
            pdf_links = []
            
            # Target links containing the PDF handler
            links = soup2.find_all('a', href=re.compile(r'handler\.axd', re.I))
            for link in links:
                label = link.get_text(strip=True)
                # Ensure it is a PDF based on the label
                if label.lower().endswith('.pdf'):
                    pdf_names.append(label)
                    pdf_links.append(urljoin(base_url, link['href']))
            
            # Join lists with a separator for the DataFrame
            results['PDF_File_Names'] = " | ".join(pdf_names) if pdf_names else None
            results['PDF_File_Links'] = " | ".join(pdf_links) if pdf_links else None
        except:
            pass

    return pd.DataFrame([results])

def scrape_oecd_groups():

    url = "https://hpvchemicals.oecd.org/ui/ChemGroup.aspx"
    
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Recommended: Keep visible to ensure JS triggers
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get(url)
        print("Page loaded. Locating 'Open all' trigger...")

        # Target the specific span that executes slider.openall()
        try:
            # Using XPath to find the span with the specific onclick attribute
            open_all_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//span[@onclick='slider.openall()']"))
            )
            # Scroll into view and click
            driver.execute_script("arguments[0].scrollIntoView();", open_all_btn)
            open_all_btn.click()
            print("Expansion triggered. Waiting for content to render...")
            time.sleep(5)  # Increased wait for all groups to expand and populate DOM
        except Exception as e:
            print(f"Could not trigger 'Open all': {e}")

        # Extract the fully rendered HTML
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        all_data = []

        # Find all group containers
        # These are identified by IDs like 'ctl00_ContentPlaceHolder1_MainXX'
        group_containers = soup.find_all('div', id=re.compile(r'Main\d+'))
        print(f"Found {len(group_containers)} group containers.")

        for container in group_containers:
            # 1. Extract and clean Group Name from the header span
            # Example ID: ctl00_ContentPlaceHolder1_L_GroupName_20
            header_span = container.find('span', id=re.compile(r'L_GroupName_'))
            if not header_span:
                continue
                
            group_raw = header_span.get_text(strip=True)
            # Remove trailing counts like '(9)' or '(4)'
            group_name = re.sub(r'\s*\(\d+\)$', '', group_raw)
            
            # 2. Extract Chemicals from the table inside the content div
            content_div = container.find('div', id=re.compile(r'-content'))
            if content_div:
                links = content_div.find_all('a', id=re.compile(r'L_SIDSNo_'))
                for link in links:
                    full_text = link.get_text(strip=True)
                    
                    # Regex to split: Name (CAS 000-00-0)
                    # Supports names with special characters and multiple dashes in CAS
                    match = re.search(r'^(.*?)\s*\(CAS\s*([\d-]+)\)$', full_text)
                    
                    if match:
                        chem_name = match.group(1).strip()
                        casrn = match.group(2).strip()
                        all_data.append({
                            "Group Name": group_name,
                            "Chemical Name": chem_name,
                            "CASRN": casrn
                        })

        return pd.DataFrame(all_data)

    finally:
        driver.quit()

if __name__ == "__main__":
    
    url = "https://hpvchemicals.oecd.org/ui/SIDS_Details.aspx?id=fc1ced8a-ce14-45fa-b003-dfeda5e38075"
    df_details = scrape_oecd_full_details(url)
    print(df_details.T)

    # out = scrape_oecd_groups()
    # out.to_parquet(config.OECD_GROUPS)

    # Execute the scraper
    # df_chemicals = scrape_oecd_chemicals()
    
    # if df_chemicals is not None:
    #     print(f"Successfully extracted {len(df_chemicals)} records.")
    #     print(df_chemicals.head())
        
    #     # Optional: Save to CSV
    #     df_chemicals.to_parquet(config.OECD_CHEMICALS, index=False)
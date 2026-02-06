# -*- coding: utf-8 -*-
"""
Created on Sat Jan 31 09:26:31 2026

@author: Gary
"""

import pandas as pd
from bs4 import BeautifulSoup
import config
import os

def process_pprtv_with_links():
    input_path = config.PPRTV_EXCEL_FILE_PATH
    base_url = "https://cfpub.epa.gov/ncea/pprtv/" # Standard EPA PPRTV base
    
    print(f"Extracting data and URLs from: {input_path}")
    
    # 1. Open and Parse
    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f, 'lxml')
    
    table = soup.find('table')
    data = []
    
    # 2. Iterate through rows
    # We skip rows that don't have enough columns to be data
    for row in table.find_all('tr'):
        cols = row.find_all(['td', 'th'])
        if len(cols) < 3:
            continue
            
        # Extract text content
        text_values = [ele.text.strip() for ele in cols]
        
        # 3. Find the URL
        # We look for the first link in the row
        link_tag = row.find('a', href=True)
        raw_url = link_tag['href'] if link_tag else None
        
        # If it's a relative URL, make it absolute
        if raw_url and not raw_url.startswith('http'):
            # This handles cases where the link might start with / or just the filename
            url = os.path.join(base_url, raw_url.lstrip('/')).replace('\\', '/')
        else:
            url = raw_url
            
        data.append({
            'Chemical_Name': text_values[1], # 'Name' is Column 1
            'CASRN': text_values[2],         # 'CASRN' is Column 2
            'URL': url
        })

    # 4. Clean up and Export
    df = pd.DataFrame(data)
    
    # Remove header row if it was scraped (where CASRN text is actually 'CASRN')
    df = df[df['CASRN'].str.upper() != 'CASRN']
    
    # Final strip of any stray whitespace
    df['CASRN'] = df['CASRN'].str.strip()
    
    print(f"Successfully processed {len(df)} chemicals with associated URLs.")
    df.to_parquet(config.PPRTV_PROCESSED, index=False)
    print(f"File saved to: {config.PPRTV_PROCESSED}")

if __name__ == "__main__":
    process_pprtv_with_links()
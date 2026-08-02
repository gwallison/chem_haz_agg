import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import re
import os
import sys

# Add the project root to the Python path to resolve the 'config' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config

def scrape_cameo_with_high_frequency_save(output_file="cameo_links_master_v3.csv", save_interval=10):
    base_url = "https://cameochemicals.noaa.gov"
    browse_url = f"{base_url}/browse"
    
    # 1. Initialize or Load existing data to resume
    if os.path.exists(output_file):
        master_df = pd.read_csv(output_file)
        # Identify chemicals already fully processed to avoid duplicates on restart
        processed_links = set(master_df['CAMEO_Link'].tolist())
        processed_letters = master_df['Letter_Group'].unique().tolist()
        print(f"Resuming. Found {len(master_df)} existing records.")
    else:
        master_df = pd.DataFrame()
        processed_links = set()
        processed_letters = []

    alphabet = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
    
    for letter in alphabet:
        # We check if the letter is in processed_letters, but we also allow 
        # resuming mid-letter by checking processed_links later.
        print(f"--- Processing Letter Group: {letter} ---")
        letter_url = f"{browse_url}/{letter}"
        
        try:
            res = requests.get(letter_url, timeout=20)
            soup = BeautifulSoup(res.text, 'html.parser')
            chemical_links = soup.select('.mainbody a[href^="/chemical/"]')
            
            current_letter_batch = []
            counter = 0

            for link_tag in chemical_links:
                detail_url = f"{base_url}{link_tag['href']}"
                
                # Skip if already in our CSV from a previous run
                if detail_url in processed_links:
                    continue

                name = link_tag.text.strip()
                time.sleep(random.uniform(2.5, 4.0)) 
                
                try:
                    detail_res = requests.get(detail_url, timeout=20)
                    d_soup = BeautifulSoup(detail_res.text, 'html.parser')
                    
                    # Logic to extract from the table structure
                    def get_table_value(header_id):
                        td = d_soup.find('td', headers=header_id)
                        if td:
                            items = [li.get_text(strip=True) for li in td.find_all('li')]
                            return "; ".join(items) if items else td.get_text(strip=True)
                        return "N/A"

                    cas_no = get_table_value('th-cas')
                    dot_label = get_table_value('th-dot')

                    new_row = {
                        "Letter_Group": letter,
                        "Chemical_Name": name,
                        "CAS No": cas_no,
                        "DOT Hazard Label": dot_label,
                        "CAMEO_Link": detail_url
                    }
                    
                    current_letter_batch.append(new_row)
                    processed_links.add(detail_url)
                    counter += 1

                    # --- TWEAK: Save every 10 data points ---
                    if counter % save_interval == 0:
                        temp_df = pd.DataFrame(current_letter_batch)
                        master_df = pd.concat([master_df, temp_df], ignore_index=True)
                        master_df.to_csv(output_file, index=False)
                        current_letter_batch = [] # Clear batch after saving
                        print(f"  Checkpoint: Saved {counter} chemicals for letter {letter}...")

                except Exception as e:
                    print(f"  Skipping {name} due to error: {e}")
            
            # Final save for any remaining chemicals in the letter group
            if current_letter_batch:
                temp_df = pd.DataFrame(current_letter_batch)
                master_df = pd.concat([master_df, temp_df], ignore_index=True)
                master_df.to_csv(output_file, index=False)
            
            print(f"--- Finished Letter {letter}. Total records: {len(master_df)} ---")

        except Exception as e:
            print(f"Critical error on Letter {letter}: {e}")

    return master_df
    
def _return_cas_lst(s):
    pattern = r'\b\d{2,7}-\d{2}-\d\b'
    outlst = []
    lst = s.split(';')
    for item in lst:
        match = re.search(pattern,item)
        if match:
            outlst.append(match.group(0))
        else:
            outlst.append('CASRN not given')
    return outlst

def clean_up_scrape():
    indf = pd.read_csv(config.CAMEO_RAW)
    caslst = []
    llst = []
    namelst = []
    dot_lst = []
    for i,row in indf.iterrows():
        clst = _return_cas_lst(row['CAS No'])
        for item in clst:
            caslst.append(item)
            llst.append(row.CAMEO_Link)
            namelst.append(row['Chemical_Name'])
            dot_lst.append(row['DOT Hazard Label'])
    outdf = pd.DataFrame({'CASRN':caslst,
                          'Chemical_Name':namelst,
                          'CAMEO_link':llst,
                          'DOT_hazard_label':dot_lst})
    outdf.to_parquet(config.CAMEO_PROCESSED)
    

        
        
if __name__ == '__main__':
    _ = scrape_cameo_with_high_frequency_save(config.CAMEO_RAW)
    clean_up_scrape()
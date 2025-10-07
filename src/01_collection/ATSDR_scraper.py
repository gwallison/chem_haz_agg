import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import re

def get_toxprofile_links(base_url):
    """
    Fetches links and their visible text from the main glossary page.
    """
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.find_all('a', href=lambda href: href and '/TSP/ToxProfiles/ToxProfiles.aspx' in href)
        
        link_data = []
        for link in links:
            url = urljoin(base_url, link.get('href'))
            text = link.get_text(strip=True)
            if text: # Only add if the chemical name is not empty
                link_data.append({'url': url, 'text': text})
        return link_data
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the main page: {e}")
        return []

def get_casrn_from_profile(profile_url):
    """
    Extracts CASRNs from a single ToxProfile page using regex.
    """
    try:
        response = requests.get(profile_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        cas_paragraph = soup.find('p', string=lambda text: text and 'CAS#' in text)
        
        if cas_paragraph:
            cas_text = cas_paragraph.get_text()
            casrn_pattern = r'\d{2,7}-\d{2}-\d'
            found_casrns = re.findall(casrn_pattern, cas_text)
            return found_casrns if found_casrns else []
            
    except requests.exceptions.RequestException as e:
        print(f"Error fetching profile page {profile_url}: {e}")
        return []

if __name__ == "__main__":
    main_url = "https://www.atsdr.cdc.gov/toxicological-profiles/glossary/index.html"
    
    print("Fetching ToxProfile links...")
    profile_link_data = get_toxprofile_links(main_url)
    
    if profile_link_data:
        print(f"Found {len(profile_link_data)} links. Now processing each link...")
        
        data_rows = []
        for link_info in profile_link_data:
            url = link_info['url']
            chemical_name = link_info['text']
            
            print(f"Processing: {chemical_name} ({url})")
            casrns = get_casrn_from_profile(url)
            
            if casrns:
                for casrn in casrns:
                    data_rows.append({
                        'ATSDR_link': url, 
                        'Chemical_Name': chemical_name, 
                        'CASRN': casrn
                    })
        
        print("\n--- Extraction Complete ---")
        
        if not data_rows:
            print("Could not extract any CASRNs.")
        else:
            df = pd.DataFrame(data_rows)
            print("\nDataFrame created successfully. First 5 rows:")
            # print(df.head())
            # print(df.columns)
            
            output_dir = r"C:/MyDocs/integrated/chem_profiles/data/02_intermediate"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "atsdr_casrn.parquet")
            
            try:
                df = df[['Chemical_Name', 'CASRN', 'ATSDR_link']]
                df.to_parquet(output_path, engine='pyarrow')
                print(f"\nSuccessfully saved the DataFrame to: {os.path.abspath(output_path)}")
            except Exception as e:
                print(f"\nError saving the Parquet file: {e}")

    else:
        print("No ToxProfile links were found on the page.")
import pandas as pd
from bs4 import BeautifulSoup
import requests
import config
import re


def scrape_niosh_cas_index(source_path, is_url=True):
    # 1. Fetch the HTML content
    if is_url:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(source_path, headers=headers)
        html_content = response.text
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
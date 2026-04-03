# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 16:19:53 2025

@author: Gary

Currently there is no offical list of the chemicals at CoC, so
we must construct it by hand.
"""
import os
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import re
import time
import numpy as np
import config

options = webdriver.ChromeOptions()
driver = webdriver.Chrome(options=options)


# in_lst = [
#     ('79-34-5', '1,1,2,2-Tetrachloroethane'),
#     ('106-93-4','1,2-Dibromoethane'),
#     ('107-06-2','1,2-Dichloroethane'),
#     ('78-87-5','1,2-Dichloropropane'),
#     ('75-07-0','Acetaldehyde'),
#     ('67-64-1','Acetone'),
#     ('75-05-8','Acetonitrile'),
#     ('107-02-8','Acrolein'),
#     ('107-13-1','Acrylonitrile'),
#     ('7440-38-2','Arsenic, inorganic compounds'),
#     ('71-43-2','Benzene'),
#     ('50-32-8','Benzo(a)pyrene'),
#     ('7440-41-7','Beryllium'),
#     ('126-99-8','beta-Chloroprene'),
#     ('106-99-0','Butadiene (1,3-Butadiene)'),
#     ('7440-43-9','Cadmium'),
#     ('75-15-0','Carbon disulfide'),
#     ('56-23-5','Carbon tetrachloride'),
#     ('7782-50-5','Chlorine'),
#     ('75-01-4','Chloroethylene; Vinyl chloride'),
#     ('67-66-3','Chloroform (Trichloromethane)'),
#     ('16065-83-1','Chromium (III) compounds'),
#     ('18540-29-9','Chromium (VI) compounds'),
#     ('75-09-2','Dichloromethane'),
#     ('64-17-5','Ethanol'),
#     ('141-78-6','Ethyl acetate'),
#     ('100-41-4','Ethylbenzene'),
#     ('75-21-8','Ethylene oxide'),
#     ('50-00-0','Formaldehyde'),
#     ('302-01-2','Hydrazine'),
#     ('7783-06-4','Hydrogen Sulfide'),
#     ('7439-92-1','Lead'),
#     ('108-31-6','Maleic Anhydride'),
#     ('7439-96-5','Manganese'),
#     ('7439-97-6','Mercury'),
#     ('74-87-3','Methyl chloride'),
#     ('110-54-3','n-Hexane'),
#     ('91-20-3','Naphthalene'),
#     ('7440-02-0','Nickel'),
#     ('10102-44-0','Nitrogen Dioxide'),
#     ('10028-15-6','Ozone'),
#     ('106-46-7','p-Dichlorobenzene'),
#     ('100-42-5','Styrene'),
#     ('127-18-4','Tetrachloroethylene'),
#     ('108-88-3','Toluene'),
#     ('584-84-9','Toluene-2,4-diisocyanate (TDI)'),
#     ('79-01-6','Trichloroethylene'),
#     ('121-44-8','Triethylamine'),
#     ('1330-20-7','Xylenes')  ]


def scrape_CofC():
    try:
        driver.get("https://environmentalhealthproject.shinyapps.io/compounds/")
        wait = WebDriverWait(driver, 20)
    
        # 1. Bypass Modal
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Close')]"))).click()
        except:
            pass
    
        # 2. Enter Compounds Area
        wait.until(EC.element_to_be_clickable((By.ID, "tile_coc"))).click()
        
        # 3. Pre-collect names
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#compound_input input")))
        raw_buttons = driver.find_elements(By.CSS_SELECTOR, "#compound_input input[type='radio']")
        compound_names = [b.get_attribute("value") for b in raw_buttons]
        
        print(f"Verified {len(compound_names)} compounds. Starting deep scrape...")
    
        compound_map = []
    
        for name in compound_names:
            try:
                # 4. Select the Compound
                selector = f"//input[@name='compound_input' and @value=\"{name}\"]"
                btn = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                driver.execute_script("arguments[0].click();", btn)
    
                # 5. Wait for the Detail Pane to update (Header check)
                # We wait until the specific name appears in the details box
                wait.until(lambda d: name.split('(')[0].strip() in d.find_element(By.ID, "compound_table").text)
    
                # 6. OPEN THE EVIDENCE TAB
                # Look for the 'Evidence' collapsible header and click it
                try:
                    evidence_header = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Evidence')]")))
                    driver.execute_script("arguments[0].click();", evidence_header)
                    # Small sleep to allow the expansion animation
                    time.sleep(0.8)
                except:
                    print(f"Warning: Could not find Evidence tab for {name}")
    
                # 7. Extract CAS Number from the now-visible HTML
                detail_pane = driver.find_element(By.ID, "compound_table")
                # We grab innerHTML specifically to ensure we see hidden/newly revealed text
                full_html = detail_pane.get_attribute('innerHTML')
                
                # Use Regex on the HTML source for maximum accuracy
                cas_match = re.search(r"CAS Number:.*?([\d-]+)", full_html, re.DOTALL)
                cas_no = cas_match.group(1).strip() if cas_match else "Not Found"
                
                compound_map.append({"Chemical Name": name, "CAS Number": cas_no})
                print(f"Extracted: {name} -> {cas_no}")
                
            except Exception as e:
                print(f"Error on {name}: {str(e)[:70]}")
                compound_map.append({"Chemical Name": name, "CAS Number": "Error"})
    
        # 8. Output
        df = pd.DataFrame(compound_map)
        # df.to_csv("environmental_compounds_cas.csv", index=False)
        print("\nScrape complete.")
    
    finally:
        driver.quit()    
    return df

def fix_missing(row):
    missing = {'Carbon tetrachloride':'56-23-5',
               'Acrylonitrile':'75-05-8',
               'Acrolein':'107-02-8',
               'Beryllium':'7440-41-7',
               'Methyl chloride':'74-87-3',
               # 'Hydrogen Sulfide':'7783-06-4',
               'Hydrogen Sulfide':'7783-06-4',
               '1,2-Dichloroethane':'107-06-2',
               'Hydrazine':'302-01-2',

               }
    if row['Chemical Name'] in missing:
        return missing[row['Chemical Name']]
    return row['CAS Number']

def generate_df():
    sdf = scrape_CofC()
    # now correct some CARN
    sdf['CAS Number'] = np.where(sdf['CAS Number'].str[0]=='0',
                                 sdf['CAS Number'].str[1:], #drop leading zero
                                 sdf['CAS Number'])
    sdf['CASRN'] = sdf.apply(lambda x: fix_missing(x),axis=1)
    # df = pd.DataFrame(in_lst,columns=['CASRN','name'])
    # outdir = r'C:/MyDocs/integrated/chem_profiles/data/02_intermediate'
    
    sdf.to_parquet(os.path.join(config.INTERMED_DATA,'Compounds_of_Concern.parquet'))
    
if __name__ == '__main__':
    generate_df()
    
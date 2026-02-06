""" This script translates ECHA's "Obligation List" into 
a usable set of H-codes for all of the authoritative CASRN.
The source data is a Excel Export from 
"https://chem.echa.europa.eu/obligation-lists/clhList"

"""

# import time
import os
# import re
# from datetime import datetime
import pandas as pd
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException, JavascriptException, NoSuchElementException
import config

def get_input_file():
    lst = os.listdir(config.RAW_DATA)
    echa_files = []
    for fn in lst:
        if fn.startswith('Harmonised_List_'):
            if fn.endswith('.xlsx'):
                echa_files.append(fn)
    echa_files.sort()
    return os.path.join(config.RAW_DATA,echa_files[-1])
      
def make_GHS_df():
    rawdf = pd.read_excel(get_input_file())
    # first process all lines keeping track of CASRN and EC Number
    casrns = []
    ecns = []
    hcodes = []
    for i,row in rawdf.iterrows():
        casrns.append(row['CAS number'])
        ecns.append(row['EC number'])
        lst = row['Hazard class, category and statement code(s)'].split('\n')
        s = ''
        for item in lst:
            slst = item.split(',')
            test_str = slst[-1].strip()
            if test_str[0] == 'H':
                s+= test_str +','
        if len(s)>0:
            s = s[:-1] #drop last comma
        hcodes.append(s)
    out = pd.DataFrame({'CASRN':casrns, 'EC_num':ecns,
                        'GHS_H_Codes':hcodes})
    out['GHS_Pictograms'] = ''
    out['GHS_Signals'] = ''
    out['GHS_P_codes'] = ''
    c = ~(out.CASRN.str[0]=='-')
    out = out[c]
    out.to_parquet(config.ECHA_HARM_OUTPUT_PATH)
    
    print(f'Processed and saved {len(out)} CAS records from ECHA')
    print(f'  -- number of duplicate CASRN: {out.CASRN.duplicated().sum()}')
if __name__ == '__main__':
    make_GHS_df()


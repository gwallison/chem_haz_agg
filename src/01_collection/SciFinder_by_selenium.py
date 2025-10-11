# -*- coding: utf-8 -*-
"""
Created on Thu Nov 21 12:24:06 2024

@author: Gary
"""
import sys
sys.path.insert(0,'c:/MyDocs/integrated/') # adjust to your setup

from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException
from selenium.common.exceptions import TimeoutException  # Import TimeoutException
import pandas as pd
import os
import time
import datetime
# import numpy  as np
from io import StringIO 
from bs4 import BeautifulSoup
import requests
import SciFinder_support as sfs
import common.master_list_manager as mlm
import config
# import openFF.common.handles as hndl


testcas = ['55845-06-2','57-11-4','1332-58-7','1338-41-6','10025-69-1',
           '11138-66-2']
outdir= r"G:\My Drive\webshare\scrape_data\SciFinder_chem_pages"
# cas_source = os.path.join(hndl.curr_repo_pkl_dir,'bgCAS.parquet')

def get_chem_frame_with_filenames(lib=outdir):
    
    lst = os.listdir(lib)
    caslst = []
    fnlst = []
    for fn in lst:
        tentcas = fn.split('_')[0]
        if tentcas.count('-')==2:
            caslst.append(tentcas)
            fnlst.append(os.path.join(lib,fn))
        else:
            # print(f'rejecting {fn}')
            pass
    
    return pd.DataFrame({'CASRN':caslst,'filename':fnlst})
    

def get_list_already_done(outdir=outdir):
    lst = os.listdir(outdir)
    caslst = []
    for fn in lst:
        tentcas = fn.split('_')[0]
        if tentcas.count('-')==2:
            caslst.append(tentcas)
    return caslst

def get_chemlist():
    done_lst = get_list_already_done(outdir)
    t = pd.read_parquet(cas_source)


    t = t[t.bgCAS.str[0].isin(['0','1','2','3','4','5','6','7','8','9'])]
    t = t[~t.bgCAS.isin(done_lst)]
    t = t.sort_values('bgCAS')
    return t.bgCAS.tolist()

def save_data(cas,text):
    nowstr = str(datetime.datetime.now())
    nowstr = nowstr.split(' ')[0]
    rootout = os.path.join(config.RAW_CAS_DIR,cas)
    fn = os.path.join(rootout,f'{cas}_SciFinder_collected_{nowstr}.html')
    with open(fn,'w', encoding='utf-8') as f:
        f.write(text)
 

def start_selenium_session():
    """
    Starts a Selenium session, logs in, and navigates directly to the
    Advanced Search page, making it ready for scraping.
    """
    # --- 1. Get Credentials from Environment Variables ---
    osu_user = os.environ.get('osu_lib_user')
    osu_pass = os.environ.get('osu_lib_passwd')
    cas_user = os.environ.get('cas_user')
    cas_pass = os.environ.get('cas_passwd')

    if not all([osu_user, osu_pass, cas_user, cas_pass]):
        print("FATAL ERROR: One or more required environment variables are not set.")
        print("Please ensure 'osu_lib_user', 'osu_lib_passwd', 'cas_user', and 'cas_passwd' are all set.")
        return None

    driver = webdriver.Chrome()
    driver.get("https://scifinder-n-cas-org.proxy.lib.ohio-state.edu/")

    try:
        # --- 2. OSU Proxy Login ---
        print("Attempting OSU proxy login...")
        user_field_osu = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        user_field_osu.send_keys(osu_user)
        pass_field_osu = driver.find_element(By.ID, "password")
        pass_field_osu.send_keys(osu_pass)
        login_button_osu = driver.find_element(By.ID, "submit")
        login_button_osu.click()
        input("Proxy login submitted. Enter when at the CAS page >")
        
        # --- 3. CAS SciFinder Login (Multi-Step) ---
        print("Attempting CAS SciFinder login...")
        user_field_cas = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        user_field_cas.send_keys(cas_user)
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "continueButton"))
        )
        next_button.click()
        print("Username submitted, proceeding to password.")
        pass_field_cas = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, "password"))
        )
        pass_field_cas.send_keys(cas_pass)
        login_button_cas = driver.find_element(By.ID, "loginButton")
        login_button_cas.click()
        print("CAS login submitted.")
        
        # --- 4. Navigate to Advanced Search Page ---
        input("Login complete. Waiting for session to establish... >> ")
        # time.sleep(10)  # A fixed wait to ensure the landing page fully loads

        print("Navigating directly to the Advanced Search page...")
        advanced_search_url = "https://scifinder-n-cas-org.proxy.lib.ohio-state.edu/advancedSearch/"
        driver.get(advanced_search_url)

        # Final confirmation: Wait for the search box to confirm we are on the right page
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, "textQuery"))
        )
        print("Successfully on Advanced Search page. Ready to begin scraping.")
        return driver

    except Exception as e:
        print(f"An unexpected error occurred during login: {e}")
        driver.quit()
        return None    
def wait_for_substance_detail_page(driver):
  """Waits for the page title to contain 'Substance Detail'.

  Args:
    driver: The Selenium webdriver instance.
  """
  try:
    WebDriverWait(driver, 60).until(EC.title_contains("Substance Detail"))
  except Exception as e:
    print(f"An error occurred waiting for Substance Detail page: {e}")
    
def click_casrn_link(driver, casrn):
  """
  On a results page, finds and clicks the link corresponding to the CASRN.
  This version searches the main document (no iframe) for the link.
  """
  print('entered click_casrn_link')
  try:
    # Based on the debug HTML, the link is in the main document.
    # We will use a simple, robust XPath to find any link containing the CASRN.
    link_locator = (By.XPATH, f"//a[contains(., '{casrn}')]")
    print(f"Searching main document for link with XPath: {link_locator[1]}")
    
    # Wait for the link element to be present.
    link_element = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located(link_locator)
    )
    print('Found link element.')

    # Use JavaScript to scroll and click for maximum reliability.
    driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
    time.sleep(0.5)
    driver.execute_script("arguments[0].click();", link_element)
    print('Clicked element using JavaScript.')

  except Exception as e:
    print(f"An error occurred in click_casrn_link: {e}")
    # If this fails again, save the page source for review.
    debug_filename = f"debug_page_for_{casrn.replace('-', '')}.html"
    with open(debug_filename, 'w', encoding='utf-8') as f:
        f.write(driver.page_source)
    print(f"Saved page source to {os.path.abspath(debug_filename)} for review.")
    raise
    

# def click_casrn_link(driver, casrn):
#   """
#   On a results page, finds and clicks the link corresponding to the CASRN.
#   This version uses a more robust locator and a JavaScript click to bypass
#   potential interference from other page elements.

#   Args:
#     driver: The Selenium webdriver instance.
#     casrn: The CASRN string to search for and click.
#   """
#   print('entered click_casrn_link')
#   try:
#     # This XPath is slightly more direct, looking for the <a> tag that contains
#     # the span with the specific CASRN.
#     link_locator = (By.XPATH, f"//a[.//span[@class='rn' and contains(., '{casrn}')]]")
    
#     # 1. Wait for the link element to simply be PRESENT in the page's HTML.
#     #    This is less strict than waiting for it to be "clickable".
#     link_element = WebDriverWait(driver, 60).until(
#         EC.presence_of_element_located(link_locator)
#     )
#     print('Found link element in page source.')

#     # 2. Use a JavaScript click, which is more reliable for complex elements.
#     driver.execute_script("arguments[0].scrollIntoView(true);", link_element)
#     time.sleep(0.5) # Small pause after scrolling
#     driver.execute_script("arguments[0].click();", link_element)
#     print('Clicked element using JavaScript.')

#   except Exception as e:
#     print(f"An error occurred in click_casrn_link: {e}")
    
def perform_advanced_search(driver, search_string):
  """
  Navigates to the Advanced Search page, enters a CASRN into the text box,
  and clicks the 'Search' button. This provides a reliable starting
  point for each chemical lookup.

  Args:
    driver: The Selenium webdriver instance.
    search_string: The CASRN to enter in the search box.
  """
  try:
    # === THIS LINE HAS BEEN ADDED BACK IN ===
    # Navigate to the Advanced Search page at the start of every search
    # to ensure we are in the correct state.
    advanced_search_url = "https://scifinder-n-cas-org.proxy.lib.ohio-state.edu/advancedSearch/"
    driver.get(advanced_search_url)
    # ========================================

    # Wait for the search input field to be ready
    search_box = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.NAME, "textQuery"))
    )
    
    # Clear the search box and enter the CASRN
    search_box.clear()  
    search_box.send_keys(search_string)
    
    # Wait for the "Search" button to be clickable and then click it.
    submit_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='Search']"))
    )
    submit_button.click()
    
    # A brief pause to allow the results page to begin loading
    time.sleep(2) 

  except Exception as e:
    print(f"An error occurred in perform_advanced_search: {e}")    
    
# def enter_search_and_submit(driver, search_string):
#   """
#   Enters the given string into the Text-Search box and submits 
#   the search, after clearing the search box.

#   Args:
#     driver: The Selenium webdriver instance.
#     search_string: The string to enter in the search box.
#   """
#   print('in enter_search_and_submit')
#   try:
#     # Find the search input field
#     search_box = driver.find_element(By.CSS_SELECTOR, "input[aria-label='Text Search']")
    
#     # Clear the search box
#     search_box.clear()  
    
#     # Enter the search string
#     search_box.send_keys(search_string)
    
#     # Find the submit button
#     submit_button = driver.find_element(By.ID, "submit-search-button")
    
#     # Click the submit button
#     submit_button.click()
#     print('submit search')
    
#     # --- START of REVISED CHANGE ---
#     # First, wait for the "Substances" tab to at least be present in the page's HTML.
#     substances_tab = WebDriverWait(driver, 20).until(
#         EC.presence_of_element_located((By.ID, "omni-nav-link-substances"))
#     )
#     print('waiting for substance button')    
#     # Second, use a JavaScript click, which is often more reliable for dynamic pages.
#     driver.execute_script("arguments[0].click();", substances_tab)
#     # ---- END of REVISED CHANGE ----
#     print('clicked substance button, wait 5 secs')
#     # Wait for the page to load (adjust the time as needed)
#     time.sleep(5)
#   except Exception as e:
#     print(f"An error occurred: {e}")
    
def expand_all_sections(driver):
    """
    I don't think this works, at least on all pages
    
    Expands all collapsible sections on the webpage, handling 
    potential 'element click intercepted' errors.

    Args:
      driver: The Selenium webdriver instance.
    """
    try:
        # Find all the collapse buttons
        collapse_buttons = driver.find_elements(By.CLASS_NAME, "accordion-toggle")

        for button in collapse_buttons:
            try:
                # First attempt: regular click
                button.click()
            except:
                # If intercepted, try scrolling into view and clicking again
                driver.execute_script("arguments[0].scrollIntoView();", button)
                time.sleep(1)
                button.click()
            time.sleep(2)
            # Add some wait time for all sections to expand (adjust as needed)

    except Exception as e:
        print(f"An error occurred: {e}")
        
def click_first_expand_all(driver):
  """Clicks the first "Expand All" button on the page, if present.

  Args:
    driver: The Selenium webdriver instance.
  """
  try:
    # Find the "Expand All" button
    expand_all_button = driver.find_element(By.CLASS_NAME, "expand-all")

    # Click the button
    expand_all_button.click()

    # Add a small wait for the sections to expand (adjust as needed)
    time.sleep(2)

  except:
    print("No 'Expand All' button found or error clicking")

def click_other_names_view_all(driver):
  """Clicks the "View All" button within the "other-names" section.

  Args:
    driver: The Selenium webdriver instance.
  """
  try:
    # Find the "other-names" section
    other_names_section = driver.find_element(By.CLASS_NAME, "other-names")

    # Find the "View All" button within the section
    view_all_button = other_names_section.find_element(By.CLASS_NAME, "toggle-link")

    # Click the button
    view_all_button.click()

    # Small wait for the content to load (adjust as needed)
    time.sleep(2)

  except:
    print("No 'View All' button found in 'other-names' section or error clicking")
     
def click_regulatory_expand_all(driver):
  """Clicks the "Expand All" button within the Regulatory Information section.

  Args:
    driver: The Selenium webdriver instance.
  """
  try:
    # Find the Regulatory Information accordion group
    regulatory_info_group = driver.find_element(By.ID, "regulatory-information")
    
    # Find the "Expand All" button within the group
    expand_all_button = regulatory_info_group.find_element(By.CLASS_NAME, "expand-all")
    
    # Click the button
    expand_all_button.click()
    
    # Small wait for sections to expand (adjust as needed)
    time.sleep(1)

  except:
    print("No 'Expand All' button found in Regulatory Information or error clicking")

def click_regulatory_view_all(driver):
  """Clicks the "View All" button within the Regulatory Information section.

  Args:
    driver: The Selenium webdriver instance.
  """
  try:
    # Find the Regulatory Information accordion group
    regulatory_info_group = driver.find_element(By.ID, "regulatory-information")
    
    # Find the "View All" button within the group
    view_all_button = regulatory_info_group.find_element(By.CLASS_NAME, "toggle")  # Assuming the class is "toggle"
    
    # Click the button
    view_all_button.click()
    
    # Small wait for the content to load (adjust as needed)
    time.sleep(1)

  except:
    print("No 'View All' button found in Regulatory Information or error clicking")  

def click_GHS_view_all(driver):
  """Clicks the "View All" button within the GHS Hazard codes section.

  Args:
    driver: The Selenium webdriver instance.
  """
  try:
    # Find the Regulatory Information accordion group
    regulatory_info_group = driver.find_element(By.ID, "ghsHazardCodes")
    
    # Find the "View All" button within the group
    view_all_button = regulatory_info_group.find_element(By.CLASS_NAME, "toggle")  # Assuming the class is "toggle"
    
    # Click the button
    view_all_button.click()
    
    # Small wait for the content to load (adjust as needed)
    time.sleep(1)

  except:
    print("No 'View All' button found in Hazards Codes Information or error clicking")        
           
        
def show_syns(driver):
    soup = BeautifulSoup(driver.page_source, "html.parser")    
    print(sfs.get_synonyms(soup))


def scrape_to_local_library(chemlist=[]):
    # does a full scrape for caslst (unless already scraped)
    # if for some reason, the process dies, it can be rerun with the same list
    
    driver = start_selenium_session()
    # Add a check to ensure login was successful before proceeding
    if driver is None:
        print("Login failed. Halting script.")
        return

    # === The navigation block that was here has been REMOVED ===
    
    alldone = get_list_already_done()
    worklist = []
    for cas in chemlist:
        if not cas in alldone:
            worklist.append(cas)
    if len(worklist)==0:
        print('Everything on your list is already in the local library!')
        
    try:
        for i,cas_from_list in enumerate(worklist):
            cas = cas_from_list.strip()
            
            print(f'\n\n**** {i+1} of {len(worklist)}:  {cas} ****\n')
            perform_advanced_search(driver,cas)
            
            try:
                WebDriverWait(driver, 5).until(EC.title_contains("Substance Detail"))
                print("Advanced search led directly to the Substance Detail page.")
                
            except TimeoutException:
                print("On a results page, attempting to find and click the CASRN link.")
                click_casrn_link(driver, cas)
                wait_for_substance_detail_page(driver)

            time.sleep(1)
            print('next click expand all')
            click_first_expand_all(driver)
            time.sleep(1)
            click_other_names_view_all(driver)
            click_regulatory_expand_all(driver)
            time.sleep(1)
            click_regulatory_view_all(driver)
            click_GHS_view_all(driver)
            
            # save_data(cas, driver.page_source)
            
            rendered_html = driver.execute_script("return document.documentElement.outerHTML;")
            save_data(cas, rendered_html)
            
    except (WebDriverException, TimeoutException)  as e:
        print(f"Disconnection or Timeout error: {e}")
        driver.quit()        
        
    
def get_new_cas_in_build(work_dir=r"C:\MyDocs\integrated\openFF\build\sandbox\work_dir"):
    newdf = pd.read_parquet(os.path.join(work_dir,'new_cas_added.parquet'))
    if len(newdf)>0:
        chemlist = newdf.CASNumber.tolist()
        scrape_to_local_library(chemlist)
        return chemlist
    else:
        return []
    
def update_from_master_list(bySource=''):
    masterdf = mlm.get_master_df()
    if len(bySource)>0:
        c = masterdf.orig_source==bySource
    else:
        c = masterdf.orig_source==masterdf.orig_source # True
    if len(masterdf[c])>0:
        chemlist = masterdf[c].CASRN.tolist()
        scrape_to_local_library(chemlist)
        return chemlist
    else:
        print(f'No chemicals classified as "{bySource}" source')
        return []
    
def build_components_list(chemlist=[],libdf=None):
    # return a list of all SciFInder components listed for items on chemlist
    
    if libdf==None:
        libdf = get_chem_frame_with_filenames()        
    complist = []    
    if len(chemlist)>0:
        print(f'getting components from {len(chemlist)} files: ',end='')
        for i,cas in enumerate(chemlist):
            print(f'**{i+1} {cas}**')
            if i%100==0: print(i,end=' ')
            fn = libdf[libdf.CASRN==cas]['filename'].values[0]
            soup = sfs.get_soup(fn)
            complist = complist + sfs.get_sub_component_substance_rn(soup)
            complist = complist+ sfs.get_component_casrn_list(soup)
        complist = list(set(complist))
        
    return complist

def add_all_new_for_builder():
    # finds and adds new cas to library, detects new components and adds any new ones
    
    chemlist = get_new_cas_in_build()
    complist = build_components_list(chemlist)
    # now add the component to the local library too
    scrape_to_local_library(complist)
        
    
def verify_all_components_are_local(lib=outdir):
    chemdf = get_chem_frame_with_filenames(lib)
    allcas = chemdf.CASRN.tolist()
    missing = set()
    for i,row in chemdf.iterrows():
        complist = build_components_list([row.CASRN])
        print(f'{row.CASRN}: {complist}')
        for cas in complist:
            if not cas in allcas:
                missing.add(cas)
                print(f'missing {cas} from {row.CASRN}')
                
    return missing

def check_all_for_download_errors(lib=outdir):
    chemdf = get_chem_frame_with_filenames(lib)
    errorlst = []
    errorfn = []
    for i,row in chemdf.iterrows():
        if i%100==0: print(f'{i+1} ',end='')
        with open(row.filename,'r') as f:
            alltxt = f.read()
        if "unexpected error has occurred" in alltxt:
            print(f'{row.CASRN} ERROR FOUND')
            errorlst.append(row.CASRN)
            errorfn.append(row.filename)
    if len(errorlst)>0:
        print(f'\n\n {len(errorlst)} ERRORS FOUND')
        q = input('Enter "delete" to remove detected files. -> ')
        if q == 'delete':
            for fn in errorfn:
                os.remove(fn)
            print('Files deleted.  Run scrape_to_local_library() with returned list')
    return errorlst

def make_full_SciFinder_output_set(lib=outdir):
    chemdf = get_chem_frame_with_filenames(lib)
    casl = []
    namel = []
    mole = []
    subn = []
    subscl = []
    poly = []
    ref = []
    ncomp = []
    comp1 = []
    comp2 = []
    
    for i,row in chemdf.iterrows():
        print(f'{i}  {row.CASRN}')
        casl.append(row.CASRN)
        soup = sfs.get_soup(row.filename)
        namel.append(sfs.get_substance_name(soup))
        mole.append(sfs.get_molecular_formula(soup))
        subn.append(sfs.get_substance_notes(soup))
        subscl.append(sfs.get_substance_classes(soup))
        poly.append(sfs.get_polymer_class_terms(soup))
        ref.append(sfs.get_number_of_references(soup))
        ncomp.append(sfs.get_number_of_components(soup))
        comp1.append(sfs.get_sub_component_substance_rn(soup))
        comp2.append(sfs.get_component_casrn_list(soup))
    outdf = pd.DataFrame({'bgCAS':casl,'sf_name':namel,'mole_form':mole,
                          'subnotes':subn,'subs_class':subscl,
                          'poly_class':poly,'numref':ref,'num_comp':ncomp,
                          'comp1':comp1,'comp2':comp2})
    outdf.to_parquet(os.path.join(lib,'scifinder_df.parquet'))
        
            
if __name__ == '__main__':
    # update_from_master_list(bySource='')
    # add_all_new_for_builder()
    # errorlst = check_all_for_download_errors()
    # missing = verify_all_components_are_local()

    scrape_to_local_library(['191-30-0'])
    
    # make_full_SciFinder_output_set()


    # lst = get_list_already_done()
    # complst = build_components_list(lst)
    
    # # get TRI data
    # fn = r"C:\Users\Gary\Downloads\ry_2024_tri_chemical_list.xlsx"
    # t = pd.read_excel(fn)
    # c = t.CASRN.str[0]!='N'
    # caslst = t[c].CASRN.unique().tolist()
    # scrape_to_local_library(caslst)


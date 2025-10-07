import requests
from bs4 import BeautifulSoup
import os
import re
import pandas as pd

OUTPUT_DIR = r"C:\MyDocs\integrated\chem_profiles\sources\collected_resources\by_casrn"

def fetch_page(url):
    """
    Fetches the HTML content of a given URL.

    Args:
        url (str): The URL of the webpage to fetch.

    Returns:
        str: The HTML content of the page as a string, or None if an error occurs.
    """
    try:
        # Using a user-agent header to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def extract_hazard_info(html_content):
    """
    Extracts the paragraph text from the 'Hazard classification & labelling' section.

    Args:
        html_content (str): The HTML content of an ECHA infocard page.

    Returns:
        str: A formatted string containing the extracted paragraph text, 
             or an empty string if the section is not found.
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, 'html.parser')

    # Find the label for the "Hazard classification & labelling" section
    hazard_label = soup.find('label', class_='aui-field-label', string=lambda t: t and 'Hazard classification & labelling' in t.strip())

    if not hazard_label:
        return "" # Section not found

    # Find the parent container of the section based on the label's position
    # The target div is two levels up from the label
    content_wrapper = hazard_label.find_parent('div', class_='aui-field-wrapper-content')
    
    if not content_wrapper:
        return "" # Could not find the main content container

    # --- Extract text from <p> tags that are direct children of the wrapper ---
    # This avoids extracting paragraphs from the nested help text section.
    # The 'recursive=False' argument is key here.
    paragraphs = content_wrapper.find_all('p', recursive=False)
    
    if not paragraphs:
        return "" # No relevant paragraphs found
        
    # Get the text from each relevant paragraph
    paragraph_texts = [p.get_text(separator=' ', strip=True) for p in paragraphs]
    
    # Join the paragraph texts with a simple newline separator
    all_text = "\n\n".join(paragraph_texts)


    # --- Format the output ---
    output = "--- Hazard Classification & Labelling ---\n\n"
    output += all_text
    
    return output

def save_hazard_summary(casrn, sub_id, hazard_text, base_dir=OUTPUT_DIR):
    """
    Cleans and saves the hazard summary text to a file in a CASRN-named subdirectory.

    Args:
        casrn (str): The CAS Registry Number for the substance.
        hazard_text (str): The raw text extracted by extract_hazard_info.
        base_dir (str): The root directory for saving the files.
    """
    if not hazard_text or not casrn:
        print("No hazard text or CASRN provided. Skipping file save.")
        return

    # --- 1. Clean up the extracted text ---
    # Remove the header line
    cleaned_text = hazard_text.replace("--- Hazard Classification & Labelling ---", "").strip()
    # Replace multiple whitespace characters (including newlines) with a single space
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

    if not cleaned_text:
        print(f"No summary text to save for CASRN {casrn}.")
        # cleaned_text = "No summary text from ECHA infocard"
        return

    # --- 2. Set up file paths ---
    casrn_dir = os.path.join(base_dir, casrn)
    file_path = os.path.join(casrn_dir, f"ECHA_Info_hazard_summary_{subid}.txt")

    # --- 3. Create the subdirectory if it doesn't exist ---
    try:
        os.makedirs(casrn_dir, exist_ok=True)
    except OSError as e:
        print(f"Error creating directory {casrn_dir}: {e}")
        return

    # --- 4. Save the cleaned text to the file ---
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        print(f"Successfully saved hazard summary to: {file_path}\n")
    except IOError as e:
        print(f"Error writing to file {file_path}: {e}")


if __name__ == '__main__':
    
    fn = r"C:\MyDocs\integrated\chem_profiles\code\data\master_cas_list.parquet"
    mastercas = pd.read_parquet(fn)
    full_cas_list = mastercas.CASRN.tolist()
    work_cas_list = []
    
    for cas in full_cas_list:
        try: 
            not_here = True
            lst = os.listdir(os.path.join(OUTPUT_DIR,cas))
            for fn in lst:
                if "ECHA_Info_hazard_sum" in fn:
                    not_here=False
                    break
        except:
            os.mkdir(os.path.join(OUTPUT_DIR,cas))
        if not_here:
            work_cas_list.append(cas)
            
    # main loop
    cols = ['Substance Information Page','exported-column-briefProfileLink',
            'exported-column-obligationsLink']
    
    for i,cas in enumerate(work_cas_list):
        print(f'Working on {cas}: {i} of {len(work_cas_list)}')
        # get substance id to generate url
        ECHAPAGES_DIR = r"C:\MyDocs\integrated\chem_profiles\code\echa_pages"
        resfn = os.path.join(ECHAPAGES_DIR,f'{cas}_search_res.csv')
        if not os.path.exists(resfn):
            print(f'No search results for {cas}')
            continue
        ids = set()
        try:
            resdf = pd.read_csv(resfn,delimiter='\t',header=2)
            t = resdf[resdf['Cas Number']==cas]
            for i,row in t.iterrows():
                for col in cols:
                    # print(col)
                    try:
                        # print(row[col])
                        ids.add(row[col].split('/')[-1])
                    except:
                        pass
                    
        except:
            pass
        
        for subid in ids:
            url = f'https://echa.europa.eu/substance-information/-/substanceinfo/{subid}'
            # Step 1: Fetch the webpage
            page_html = fetch_page(url)
            
            if page_html:
                # Step 2: Extract the information
                hazard_data = extract_hazard_info(page_html)
                
                if hazard_data:
                    # print(hazard_data)
                    # Step 3: Save the data to a file
                    save_hazard_summary(cas, subid, hazard_data)
                else:
                    print("Hazard classification & labelling section not found on the page.")
                    save_hazard_summary(cas, subid, "NO ECHA SUMMARY DATA")
                    
        
            
    
    
    
    
    # # --- Example 1: A substance with the hazard section ---
    # print("--- Processing Formaldehyde (CAS 50-00-0) ---")
    # formaldehyde_cas = '50-00-0'
    # formaldehyde_url = f'https://echa.europa.eu/substance-information/-/substanceinfo/100.000.002'
    
    # # Step 1: Fetch the webpage
    # page_html = fetch_page(formaldehyde_url)
    
    # if page_html:
    #     # Step 2: Extract the information
    #     hazard_data = extract_hazard_info(page_html)
        
    #     if hazard_data:
    #         print(hazard_data)
    #         # Step 3: Save the data to a file
    #         save_hazard_summary(formaldehyde_cas, hazard_data)
    #     else:
    #         print("Hazard classification & labelling section not found on the page.")

    # print("\n" + "="*50 + "\n")

    # # --- Example 2: A substance that may not have the section (for testing) ---
    # print("--- Processing Water (CAS 7732-18-5) ---")
    # water_cas = '7732-18-5'
    # water_url = f'https://echa.europa.eu/substance-information/-/substanceinfo/100.028.349'
    
    # page_html = fetch_page(water_url)

    # if page_html:
    #     hazard_data = extract_hazard_info(page_html)
        
    #     if hazard_data:
    #         print(hazard_data)
    #         save_hazard_summary(water_cas, hazard_data)
    #     else:
    #         print("Hazard classification & labelling section not found on the page.")


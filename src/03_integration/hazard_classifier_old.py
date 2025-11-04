import pandas as pd
import config
import os

# from master_list_manager import MASTER_FILE_PATH
from config import GHS_CONSOLIDATED_DATA_PATH, MASTER_CAS_LIST
from config import TIER_1_CLASSIFICATION_OUTPUT_PATH
from config import HAZARD_MAP

# --- 2. Define Hazard Codes and Final Output Path ---

def find_matching_codes(series: pd.Series, codes_to_find: list) -> pd.Series:
    """
    A vectorized function to find all specified H-codes within a series of strings.
    """
    # Creates a regex pattern like r'\b(H350|H351|...)\b' to match whole codes
    pattern = r'\b(' + '|'.join(codes_to_find) + r')\b'
    # Finds all matches, then for each list of matches, sorts them uniquely and joins
    return series.str.findall(pattern).apply(lambda x: '; '.join(sorted(list(set(x)))))

def lst_to_str(lst):
    s = ''
    for item in lst:
        if not item: 
            s += ' '
        else: # len(item)>0:
            s += item+' '
    return s

def generate_tier_1_classifications(sources=['PubChem','ChemInformatics',
                                             'ECHA Harmonized','Australia',
                                             'Japan']):
    """
    Loads data from all sources, classifies chemicals based on Tier 1 H-codes,
    and saves a consolidated output file.
    """
    print("--- Starting Hazard Classification Generation ---")

    # ... (The data loading part of your function is correct and unchanged) ...
    print("Loading source data files...")
    ghsdf = pd.read_parquet(GHS_CONSOLIDATED_DATA_PATH)
    ghsdf = ghsdf[ghsdf.source.isin(sources)]
    cons_ghs = ghsdf.groupby('CASRN',as_index=False)['GHS_H_Codes'].apply(list)
    cons_ghs['all_hcodes'] = cons_ghs.GHS_H_Codes.map(lambda x: lst_to_str(x))
    mcas = pd.read_parquet(MASTER_CAS_LIST).CASRN.unique().tolist()
    cons_ghs = cons_ghs[cons_ghs.CASRN.isin(mcas)]
    

    output_df = cons_ghs[['CASRN']].copy()
    
    # MODIFIED: Renamed 'codes' to 'codes_dict' for clarity
    for category, codes_dict in HAZARD_MAP.items():
        print(f"Classifying for {category} hazards...")
        
        # MODIFIED: Explicitly select the list of codes from the '1' key
        codes_to_find = codes_dict['1']
        
        # Find matching codes using the correct list
        allcodes = find_matching_codes(cons_ghs['all_hcodes'], codes_to_find)

        # ... (The rest of your function is correct and unchanged) ...
        output_df[f'{category}_source_codes'] = allcodes.str.replace(r'(;)+', ';', regex=True)\
                                                                 .str.strip(';')\
                                                                 .apply(lambda x: '; '.join(sorted(list(set(x.split('; '))))))
        output_df[f'is_{category}'] = output_df[f'{category}_source_codes'].str.len()>1                                                         
    
    output_df.to_parquet(TIER_1_CLASSIFICATION_OUTPUT_PATH, index=False)
    print(f"\n✅ Hazard classification complete. Results saved to '{TIER_1_CLASSIFICATION_OUTPUT_PATH}'")

# --- Main Execution Block ---
if __name__ == "__main__":
    generate_tier_1_classifications()
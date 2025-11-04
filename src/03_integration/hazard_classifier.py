import pandas as pd
import config
import os
import re

# from master_list_manager import MASTER_FILE_PATH
from config import GHS_CONSOLIDATED_DATA_PATH, MASTER_CAS_LIST
from config import GHS_CLASSIFICATION_OUTPUT_PATH
from config import HAZARD_MAP
from config import GHS_EVIDENCE_PATH

# --- 2. Define Hazard Codes and Final Output Path ---

def find_matching_codes(series: pd.Series, codes_to_find: list) -> pd.Series:
    """
    A vectorized function to find all specified H-codes within a series of strings.
    """
    # Creates a regex pattern like r'\b(H350|H351|...)\b' to match whole codes
    pattern = r'\b(' + '|'.join(codes_to_find) + r')\b'
    # Finds all matches, then for each list of matches, sorts them uniquely and joins
    return series.str.findall(pattern).apply(lambda x: '; '.join(sorted(list(set(x)))))

def _generate_ghs_evidence_log(ghsdf: pd.DataFrame, hazard_map: dict) -> pd.DataFrame:
    """
    Scans the un-aggregated GHS data and logs all Tier 1 and Tier 2 evidence.
    """
    print("--- Generating GHS evidence log (Tiers 1 & 2) ---")
    all_evidence = []
    
    ghsdf['GHS_H_Codes'] = ghsdf['GHS_H_Codes'].fillna('')
    
    for category, codes_dict in hazard_map.items():
        tier1_codes = codes_dict.get('1', [])
        tier2_codes = codes_dict.get('2', [])
        
        if not tier1_codes and not tier2_codes:
            continue
            
        print(f"  - Logging GHS evidence for {category}")
        
        temp_df = ghsdf[['CASRN', 'source', 'GHS_H_Codes']].copy()
        
        # --- Process Tier 1 Codes ---
        if tier1_codes:
            pattern1 = re.compile(r'\b(' + '|'.join(tier1_codes) + r')\b')
            temp_df['matches'] = temp_df['GHS_H_Codes'].apply(lambda x: pattern1.findall(str(x)))
            exploded1 = temp_df.explode('matches').dropna(subset=['matches'])
            
            if not exploded1.empty:
                exploded1 = exploded1.rename(columns={'matches': 'actual_value'})
                exploded1['data_source'] = exploded1['source']
                exploded1['value_type'] = 'hcode'
                exploded1['associated_tier'] = 'Tier 1' 
                exploded1['hazard_category'] = category
                all_evidence.append(
                    exploded1[['CASRN', 'data_source', 'value_type', 
                             'associated_tier', 'actual_value', 'hazard_category']]
                )

        # --- Process Tier 2 Codes ---
        if tier2_codes:
            pattern2 = re.compile(r'\b(' + '|'.join(tier2_codes) + r')\b')
            temp_df['matches'] = temp_df['GHS_H_Codes'].apply(lambda x: pattern2.findall(str(x)))

            # --- DEBUGGING STEP: Check if any T2 matches are found ---
            pre_explode_matches = temp_df[temp_df['matches'].apply(len) > 0]
            if not pre_explode_matches.empty:
                print(f"    DEBUG: Found {len(pre_explode_matches)} rows with Tier 2 H-codes for {category}.")
            else:
                # This will print if no matches are found for a category
                print(f"    DEBUG: No rows found with Tier 2 H-codes for {category}.")
            # --- END DEBUGGING STEP ---
            
            exploded2 = temp_df.explode('matches').dropna(subset=['matches'])
            
            if not exploded2.empty:
                exploded2 = exploded2.rename(columns={'matches': 'actual_value'})
                exploded2['data_source'] = exploded2['source']
                exploded2['value_type'] = 'hcode'
                exploded2['associated_tier'] = 'Tier 2'
                exploded2['hazard_category'] = category
                all_evidence.append(
                    exploded2[['CASRN', 'data_source', 'value_type', 
                             'associated_tier', 'actual_value', 'hazard_category']]
                )

    if not all_evidence:
        print("No GHS evidence found.")
        return pd.DataFrame(columns=['CASRN', 'data_source', 'value_type', 
                                      'associated_tier', 'actual_value', 'hazard_category'])

    final_evidence_df = pd.concat(all_evidence, ignore_index=True)
    # --- MODIFICATION: Added drop_duplicates just in case ---
    final_evidence_df = final_evidence_df.drop_duplicates().reset_index(drop=True)
    print(f"✅ GHS evidence log generated with {len(final_evidence_df)} records.")
    return final_evidence_df

def lst_to_str(lst):
    s = ''
    for item in lst:
        if not item: 
            s += ' '
        else: # len(item)>0:
            s += item+' '
    return s

def generate_ghs_classifications(sources=['PubChem','ChemInformatics',
                                          'ECHA Harmonized','Australia',
                                          'Japan']):
    """
    Loads data from all sources, classifies chemicals based on Tier 1 AND Tier 2
    H-codes, and saves a consolidated output file.
    
    Also generates a detailed GHS evidence log.
    """
    print("--- Starting GHS Classification Generation ---")

    print("Loading source data files...")
    ghsdf = pd.read_parquet(GHS_CONSOLIDATED_DATA_PATH)
    ghsdf = ghsdf[ghsdf.source.isin(sources)]
    
    # --- Generate and save the GHS evidence log *before* aggregating ---
    evidence_df = _generate_ghs_evidence_log(ghsdf, HAZARD_MAP)
    evidence_df.to_parquet(GHS_EVIDENCE_PATH, index=False)
    print(f"✅ GHS evidence log saved to '{GHS_EVIDENCE_PATH}'")
    
    # --- Continue with existing aggregation logic ---
    cons_ghs = ghsdf.groupby('CASRN',as_index=False)['GHS_H_Codes'].apply(list)
    cons_ghs['all_hcodes'] = cons_ghs.GHS_H_Codes.map(lambda x: lst_to_str(x))
    mcas = pd.read_parquet(MASTER_CAS_LIST).CASRN.unique().tolist()
    cons_ghs = cons_ghs[cons_ghs.CASRN.isin(mcas)]
    
    output_df = cons_ghs[['CASRN']].copy()
    
    # --- MODIFICATION START: Generate T1 and T2 flags ---
    for category, codes_dict in HAZARD_MAP.items():
        print(f"Classifying for {category} hazards...")
        
        # --- Process Tier 1 codes ---
        codes_to_find_t1 = codes_dict.get('1', [])
        allcodes_t1 = find_matching_codes(cons_ghs['all_hcodes'], codes_to_find_t1)
        output_df[f'{category}_source_codes_t1'] = allcodes_t1.str.replace(r'(;)+', ';', regex=True)\
                                                                 .str.strip(';')\
                                                                 .apply(lambda x: '; '.join(sorted(list(set(x.split('; '))))))
        output_df[f'is_{category}_tier1'] = output_df[f'{category}_source_codes_t1'].str.len()>1                                                         

        # --- Process Tier 2 codes ---
        codes_to_find_t2 = codes_dict.get('2', [])
        allcodes_t2 = find_matching_codes(cons_ghs['all_hcodes'], codes_to_find_t2)
        output_df[f'{category}_source_codes_t2'] = allcodes_t2.str.replace(r'(;)+', ';', regex=True)\
                                                                 .str.strip(';')\
                                                                 .apply(lambda x: '; '.join(sorted(list(set(x.split('; '))))))
        output_df[f'is_{category}_tier2'] = output_df[f'{category}_source_codes_t2'].str.len()>1                                                         
    # --- MODIFICATION END ---
    
    # --- MODIFICATION: Save to new output path ---
    output_df.to_parquet(GHS_CLASSIFICATION_OUTPUT_PATH, index=False)
    print(f"\n✅ GHS classification complete. Results saved to '{GHS_CLASSIFICATION_OUTPUT_PATH}'")

# --- Main Execution Block ---
if __name__ == "__main__":
    generate_ghs_classifications()
import pandas as pd
import numpy as np
import os
import re 

from config import MASTER_CAS_LIST
from config import HAZARD_MAP
from config import ECHA_INDUS_OUTPUT_PATH

# --- MODIFICATION START: Updated config imports ---
from config import CHEMINFO_HAZARD_SUMMARY_PATH 
from config import FINAL_TIERED_OUTPUT_PATH 
from config import CHEMINFO_CATEGORY_MAP 

try:
    # --- Use the new GHS classification file ---
    from config import GHS_CLASSIFICATION_OUTPUT_PATH
    from config import GHS_EVIDENCE_PATH
    from config import MASTER_EVIDENCE_LOG_PATH
except ImportError:
    print("Warning: Config paths not found. Using defaults.")
    # This path MUST match the output from hazard_classifier.py
    GHS_CLASSIFICATION_OUTPUT_PATH = 'data/processed/ghs_classification.parquet'
    GHS_EVIDENCE_PATH = 'data/processed/ghs_evidence_log.parquet'
    MASTER_EVIDENCE_LOG_PATH = 'data/processed/master_evidence_log.parquet'
# --- MODIFICATION END ---


def prepare_data_for_tiering():
    """
    Loads and merges all necessary data sources into a single DataFrame.
    """
    print("--- Preparing data for tiered classification ---")
    all_evidence = []
    
    try:
        master_df = pd.read_parquet(MASTER_CAS_LIST)[['CASRN']]
        ghs_class_df = pd.read_parquet(GHS_CLASSIFICATION_OUTPUT_PATH)
        echa_df = pd.read_parquet(ECHA_INDUS_OUTPUT_PATH)[['CASRN', 'GHS_H_Codes']].fillna('')
        cheminfo_raw_df = pd.read_parquet(CHEMINFO_HAZARD_SUMMARY_PATH)
        ghs_evidence_log = pd.read_parquet(GHS_EVIDENCE_PATH)
        all_evidence.append(ghs_evidence_log)
        
    except FileNotFoundError as e:
        print(f"❌ Error: A required source file was not found: {e.filename}")
        return None, None

    print("Merging data sources and generating summaries/evidence for all hazard categories...")
    
    df = master_df.merge(ghs_class_df, on='CASRN', how='left').merge(echa_df, on='CASRN', how='left')
    
    # Define mapping for ChemInformatics data (unchanged)
    code_map = {'VH': 'tox', 'H': 'tox', 'M': 'lo', 'L': 'lo', 'I': 'unk', 'ND': 'unk'}
    tier_map = {'VH': 'Tier 2', 'H': 'Tier 2', 'M': 'Tier 3', 'L': 'Tier 3'}


    for category, codes_dict in HAZARD_MAP.items():
        print(f"  - Processing {category}...")
        
        # --- ChemInformatics Logic (with data cleaning and correct hierarchy) ---
        if category in CHEMINFO_CATEGORY_MAP:
            cheminfo_cats = CHEMINFO_CATEGORY_MAP[category]
            valid_cats = [c for c in cheminfo_cats if c in cheminfo_raw_df.columns]
            if not valid_cats:
                df[f'cheminfo_{category}_summary'] = 'unk'
            else:
                temp_cheminfo = cheminfo_raw_df[['CASRN'] + valid_cats].copy()
                
                # 1. Generate Evidence Log
                melted_df = temp_cheminfo.melt(id_vars='CASRN', 
                                               value_vars=valid_cats, 
                                               var_name='hazard_category_raw', 
                                               value_name='actual_value')
                melted_df = melted_df.dropna(subset=['actual_value'])
                
                # Clean data before filtering
                melted_df['actual_value'] = melted_df['actual_value'].astype(str).str.strip().str.upper()
                
                # Filter to only codes that map to a tier
                melted_df = melted_df[melted_df.actual_value.isin(tier_map.keys())]
                
                if not melted_df.empty:
                    melted_df['associated_tier'] = melted_df['actual_value'].map(tier_map)
                    melted_df['data_source'] = 'ChemInfoHazard'
                    melted_df['value_type'] = 'civar_code'
                    melted_df['hazard_category'] = category
                    all_evidence.append(
                        melted_df[['CASRN', 'data_source', 'value_type', 'associated_tier',
                                   'actual_value', 'hazard_category', 'hazard_category_raw']]
                    )

                # 2. Generate Summary Column for Tiering Logic
                for col in valid_cats: 
                    # Clean data before mapping
                    temp_cheminfo[col] = temp_cheminfo[col].astype(str).str.strip().str.upper()
                    # Map cleaned codes, fill any non-matches with 'unk'
                    temp_cheminfo[col] = temp_cheminfo[col].map(code_map).fillna('unk')
                
                # Correct hierarchy (Tox > Unk > Lo)
                conditions = [
                    (temp_cheminfo[valid_cats] == 'tox').any(axis=1),
                    (temp_cheminfo[valid_cats] == 'unk').any(axis=1)
                ]
                choices = ['tox', 'unk']
                # If neither 'tox' nor 'unk' is found, it defaults to 'lo'
                summary_series = np.select(conditions, choices, default='lo')
                
                summary_df = pd.DataFrame({
                    'CASRN': temp_cheminfo['CASRN'],
                    f'cheminfo_{category}_summary': summary_series
                }).drop_duplicates()
                
                df = df.merge(summary_df, on='CASRN', how='left')
                df[f'cheminfo_{category}_summary'] = df[f'cheminfo_{category}_summary'].fillna('unk')
        else:
            df[f'cheminfo_{category}_summary'] = 'unk'
          
        # --- Tier 2 (ECHA INDUS) Logic (Unchanged) ---
        print(f"  - Checking INDUS H-codes for {category}...")
        
        tier1_h_codes = codes_dict.get('1', [])
        tier2_h_codes = codes_dict.get('2', []) 
        all_mapped_codes = tier1_h_codes + tier2_h_codes
        
        temp_echa = echa_df[['CASRN', 'GHS_H_Codes']].copy()

        if all_mapped_codes:
            pattern_str = r'\b(?:' + '|'.join(all_mapped_codes) + r')\b'
            pattern = re.compile(pattern_str)
            
            # 1. Generate Evidence Log
            temp_echa['matches'] = temp_echa['GHS_H_Codes'].apply(lambda x: pattern.findall(str(x)))
            exploded = temp_echa.explode('matches').dropna(subset=['matches'])
            
            if not exploded.empty:
                exploded = exploded.rename(columns={'matches': 'actual_value'})
                exploded['data_source'] = 'ECHA INDUS'
                exploded['value_type'] = 'hcode'
                exploded['associated_tier'] = 'Tier 2' 
                exploded['hazard_category'] = category
                all_evidence.append(
                    exploded[['CASRN', 'data_source', 'value_type', 
                               'associated_tier', 'actual_value', 'hazard_category']]
                )
            
            # 2. Generate *single* Flag for Tiering Logic
            df[f'indus_has_{category}_mapped_code'] = df['GHS_H_Codes'].str.contains(pattern_str, regex=True, na=False)
        else:
            df[f'indus_has_{category}_mapped_code'] = False
        
    # --- Combine all evidence logs (Unchanged) ---
    if not all_evidence:
        print("Warning: No evidence was found in any source.")
        final_evidence_log = pd.DataFrame(
            columns=['CASRN', 'data_source', 'value_type', 'associated_tier', 
                     'actual_value', 'hazard_category', 'hazard_category_raw']
        )
    else:
        final_evidence_log = pd.concat(all_evidence, ignore_index=True)
        final_evidence_log = final_evidence_log.drop_duplicates().reset_index(drop=True)
        
    return df, final_evidence_log


def calculate_tiers(df: pd.DataFrame, category: str) -> pd.Series:
    """Applies the tiered classification logic for a given hazard category."""
    
    # --- GHS column names ---
    is_t1_col = f'is_{category}_tier1'
    is_t2_col = f'is_{category}_tier2'
    
    # --- New single INDUS column name ---
    indus_mapped_col = f'indus_has_{category}_mapped_code'
    
    cheminfo_col = f'cheminfo_{category}_summary'
    
    # Handle cases where columns might not exist
    if is_t1_col not in df.columns:
        df[is_t1_col] = False
    if is_t2_col not in df.columns:
        df[is_t2_col] = False
    if indus_mapped_col not in df.columns:
        df[indus_mapped_col] = False
    if cheminfo_col not in df.columns:
        df[cheminfo_col] = 'unk'
        
    # Fill NaN values from left merges and set correct type
    df[is_t1_col] = df[is_t1_col].fillna(False).astype(bool)
    df[is_t2_col] = df[is_t2_col].fillna(False).astype(bool)
    df[cheminfo_col] = df[cheminfo_col].fillna('unk')


    conditions = [
        (df[is_t1_col] == True),                             # Tier 1: Harmonized T1 code
        (df[is_t2_col] == True),                             # Tier 2: Harmonized T2 code
        (df[indus_mapped_col] == True),                      # Tier 2: INDUS (T1 or T2 code)
        (df[cheminfo_col] == 'tox'),                         # Tier 2: ChemInfo 'tox'
        (df[is_t1_col] == False) &                           # Tier 3: No T1/T2 triggers
         (df[is_t2_col] == False) & 
         (df[indus_mapped_col] == False) & 
         (df[cheminfo_col] == 'lo')
    ]
    choices = ['Tier 1', 'Tier 2', 'Tier 2', 'Tier 2', 'Tier 3']
    return np.select(conditions, choices, default='Tier 4')


def generate_tiered_classification():
    """
    Main orchestration function to run the entire tiered classification process.
    """
    prepared_df, evidence_log = prepare_data_for_tiering()
    
    if prepared_df is None:
        print("Tiered classification aborted due to missing data.")
        return
        
    print("\n--- Applying tiered classification logic ---")
    
    final_df = prepared_df[['CASRN']].copy()
    
    categories_to_run = list(HAZARD_MAP.keys())
    for cat in categories_to_run:
        print(f"Calculating tiers for {cat}...")
        final_df[f'{cat}_Tier'] = calculate_tiers(prepared_df, cat)
        
    final_df.to_parquet(FINAL_TIERED_OUTPUT_PATH, index=False)
    print(f"\n✅ Tiered classification complete. Final results saved to '{FINAL_TIERED_OUTPUT_PATH}'")

    if evidence_log is not None:
        evidence_log.to_parquet(MASTER_EVIDENCE_LOG_PATH, index=False)
        print(f"✅ Master evidence log saved ({len(evidence_log)} records) to '{MASTER_EVIDENCE_LOG_PATH}'")

    print("\n--- Final Tier Summary ---")
    for cat in categories_to_run:
        print(f"\n-- {cat} Tier Counts --")
        print(final_df[f'{cat}_Tier'].value_counts().sort_index())
        
# --- Main Execution Block ---
if __name__ == "__main__":
    generate_tiered_classification()
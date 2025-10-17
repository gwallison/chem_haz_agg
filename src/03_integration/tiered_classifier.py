import pandas as pd
import numpy as np
import os

from config import MASTER_CAS_LIST
from config import HAZARD_MAP, TIER_1_CLASSIFICATION_OUTPUT_PATH
from config import ECHA_INDUS_OUTPUT_PATH
from config import CHEMINFO_HAZARD_OUTPUT_PATH, CHEMINFO_HAZARD_SUMMARY_PATH

from config import FINAL_TIERED_OUTPUT_PATH 
from config import CHEMINFO_CATEGORY_MAP 



def summarize_hazard_data(
    hazard_df: pd.DataFrame,
    output_path: str,
    categories: list = ['Carcinogenicity', 'Genotoxicity_Mutagenicity', 
                        'Reproductive']
) -> pd.DataFrame:
    """
    Summarizes EPA hazard codes from specific categories into a single code ('tox', 'lo', 'unk').

    Args:
        hazard_df (pd.DataFrame): The input DataFrame from process_hazard_xlsx_files.
        output_path (str): The path to save the summarized Parquet file.
        categories (list): A list of hazard columns to consider for the summary.

    Returns:
        pd.DataFrame: A DataFrame with CASRN and the new summary code.
    """
    print("\n--- Summarizing ChemInformatics Hazard Codes ---")
    
    # Check if all requested categories are in the DataFrame
    missing_cats = [cat for cat in categories if cat not in hazard_df.columns]
    if missing_cats:
        print(f"❌ Error: The following categories were not found in the DataFrame: {missing_cats}")
        return

    # Create a temporary DataFrame with just the categories of interest
    summary_df = hazard_df[['CASRN'] + categories].copy()
    
    # Define the mapping from EPA codes to our summary codes
    code_map = {'VH': 'tox', 'H': 'tox', 'M': 'lo', 'L': 'lo', 'I': 'unk', 'ND': 'unk'}
    
    # Apply the mapping to all category columns at once
    for cat in categories:
        summary_df[cat] = summary_df[cat].map(code_map).fillna('unk')
        
    # Use numpy.select for efficient, conditional logic to create the final code
    conditions = [
        (summary_df[categories] == 'tox').any(axis=1),
        (summary_df[categories] == 'unk').any(axis=1)
    ]
    choices = ['tox', 'unk']
    
    summary_df['hazard_summary_code'] = np.select(conditions, choices, default='lo')
    
    # Prepare the final output DataFrame
    final_df = summary_df[['CASRN', 'hazard_summary_code']]
    final_df.to_parquet(output_path, index=False)
    print(f"✅ Hazard summary complete. Saved {len(final_df)} records to {output_path}")
    
    return final_df


def prepare_data_for_tiering():
    """Loads and merges all necessary data sources into a single DataFrame."""
    print("--- Preparing data for tiered classification ---")
    # ... (try/except block for loading data is unchanged) ...
    try:
        master_df = pd.read_parquet(MASTER_CAS_LIST)[['CASRN']]
        tier1_df = pd.read_parquet(TIER_1_CLASSIFICATION_OUTPUT_PATH)
        echa_df = pd.read_parquet(ECHA_INDUS_OUTPUT_PATH)[['CASRN', 'GHS_H_Codes']]
        cheminfo_df = pd.read_parquet(CHEMINFO_HAZARD_SUMMARY_PATH)
    except FileNotFoundError as e:
        print(f"❌ Error: A required source file was not found: {e.filename}")
        return None


    print("Merging data sources and generating summaries for all hazard categories...")
    df = master_df.merge(tier1_df, on='CASRN', how='left').merge(echa_df, on='CASRN', how='left')
    # print(df.columns)

    # MODIFIED: Renamed 'h_codes' to 'codes_dict' for clarity
    for category, codes_dict in HAZARD_MAP.items():
        print(category, codes_dict)
        if category in CHEMINFO_CATEGORY_MAP:
            print(f"  - Generating ChemInfo summary for {category}...")
            summary = summarize_hazard_data(
                hazard_df=cheminfo_df, output_path=None,
                categories=CHEMINFO_CATEGORY_MAP[category]
            ).rename(columns={'hazard_summary_code': f'cheminfo_{category}_summary'})
            df = df.merge(summary, on='CASRN', how='left')
          
        # Generate the boolean INDUS code flag for the current category
        print(f"  - Checking INDUS H-codes for {category}...")
        
        # MODIFIED: Explicitly select the list of Tier 1 H-codes from the dictionary
        tier1_h_codes = codes_dict['1']
        
        # Use the correct list to build the pattern
        pattern = '|'.join(tier1_h_codes)
        df[f'indus_has_{category}_code'] = df['GHS_H_Codes'].fillna('').str.contains(pattern)
        
    return df

def calculate_tiers(df: pd.DataFrame, category: str) -> pd.Series:
    """Applies the tiered classification logic for a given hazard category."""
    # This function is already general and requires no changes.
    is_col = f'is_{category}'
    indus_col = f'indus_has_{category}_code'
    cheminfo_col = f'cheminfo_{category}_summary'
    
    # Handle cases where a category might not have a cheminfo summary
    if cheminfo_col not in df.columns:
        df[cheminfo_col] = np.nan

    conditions = [
        (df[is_col] == True),
        (df[indus_col] == True),
        (df[cheminfo_col] == 'tox'),
        (df[indus_col] == False) & (df[cheminfo_col] == 'lo')
    ]
    choices = ['Tier 1', 'Tier 2', 'Tier 2', 'Tier 3']
    return np.select(conditions, choices, default='Tier 4')

def generate_tiered_classification():
    """
    Main orchestration function to run the entire tiered classification process.
    """
    prepared_df = prepare_data_for_tiering()
    
    if prepared_df is None:
        print("Tiered classification aborted due to missing data.")
        return
        
    print("\n--- Applying tiered classification logic ---")
    
    final_df = prepared_df[['CASRN']].copy()
    
    # MODIFIED: Get the list of categories directly from the imported HAZARD_MAP.
    categories_to_run = list(HAZARD_MAP.keys())
    for cat in categories_to_run:
        print(f"Calculating tiers for {cat}...")
        final_df[f'{cat}_Tier'] = calculate_tiers(prepared_df, cat)
        

    final_df.to_parquet(FINAL_TIERED_OUTPUT_PATH, index=False)
    print(f"\n✅ Tiered classification complete. Final results saved to '{FINAL_TIERED_OUTPUT_PATH}'")

    print("\n--- Final Tier Summary ---")
    for cat in categories_to_run:
        print(f"\n-- {cat} Tier Counts --")
        print(final_df[f'{cat}_Tier'].value_counts().sort_index())

# --- Main Execution Block ---
if __name__ == "__main__":
    generate_tiered_classification()
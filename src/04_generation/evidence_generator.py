# -*- coding: utf-8 -*-
"""
Created on Tue Oct 21 13:06:33 2025

@author: Gary
"""

import pandas as pd
import functools
import json
import os
import re

# --- Configuration ---
# Assuming config.py is in a parent directory or PYTHONPATH
try:
    from config import MASTER_EVIDENCE_LOG_PATH
    from config import GHS_CODES_URL
    
except ImportError:
    print("Warning: Config paths not found. Using defaults.")
    MASTER_EVIDENCE_LOG_PATH = 'data/processed/master_evidence_log.parquet'
    GHS_CODES_URL = 'https://raw.githubusercontent.com/Open-FF-data/Open-FF-storage/main/ghs_h_codes.csv'

from config import FINAL_TIERED_OUTPUT_PATH
# --- Caching Function ---

@functools.lru_cache(maxsize=None)
def _get_evidence_lookup_data():
    """
    Internal helper function to load and cache evidence data.
    Loads the master evidence log, GHS code descriptions, and final tier data.
    """
    print("--- Loading evidence log, GHS codes, and final tiers (first-time only) ---")
    
    # 1. Load Master Evidence Log
    try:
        evidence_df = pd.read_parquet(MASTER_EVIDENCE_LOG_PATH)
    except FileNotFoundError:
        print(f"❌ Error: Master evidence log not found at {MASTER_EVIDENCE_LOG_PATH}")
        evidence_df = pd.DataFrame(columns=['CASRN', 'hazard_category', 'actual_value', 'value_type', 'data_source', 'hazard_category_raw', 'associated_tier'])

    # 2. Load GHS Code Descriptions
    try:
        tables = pd.read_html(GHS_CODES_URL)
        ghs_df = tables[0] 
        ghs_lookup = pd.Series(
            ghs_df['Hazard Statements'].values, 
            index=ghs_df['H-Code']
        ).to_dict()
    except Exception as e:
        print(f"⚠️ Warning: Could not load GHS descriptions from {GHS_CODES_URL}. Descriptions will be blank. Error: {e}")
        ghs_lookup = {}
        
    # 3. Load Final Tier Classifications
    try:
        final_tier_df = pd.read_parquet(FINAL_TIERED_OUTPUT_PATH)
    except FileNotFoundError:
        print(f"❌ Error: Final tier classifications not found at {FINAL_TIERED_OUTPUT_PATH}")
        final_tier_df = pd.DataFrame(columns=['CASRN'])

    return evidence_df, ghs_lookup, final_tier_df

# --- Main Function ---

def get_evidence_for_casrn(casrn: str) -> (dict, dict):
    """
    Retrieves formatted evidence for a given CASRN, filtered to include
    only the evidence that matches the final calculated tier for each category.
    
    Args:
        casrn (str): The CASRN to look up.

    Returns:
        tuple (dict, dict): 
            1. A dictionary of formatted evidence strings.
            2. A dictionary of the final tiers for each category (e.g., {'CMR': 'Tier 1'}).
    """
    # 1. Load cached data (now returns 3 items)
    evidence_df, ghs_lookup, final_tier_df = _get_evidence_lookup_data()
    
    # 2. Get Final Tiers for the specific CASRN
    cas_tiers_row = final_tier_df[final_tier_df.CASRN == casrn]
    if cas_tiers_row.empty:
        # Return empty dicts for both
        return {"error": f"CASRN '{casrn}' not found in the final tier classification file."}, {}
    
    # Convert tier row to a lookup dict, e.g., {'CMR_Tier': 'Tier 1', ...}
    cas_tiers_dict = cas_tiers_row.iloc[0].to_dict()

    # --- NEW: Create a simple tier lookup to return ---
    # e.g., {'CMR': 'Tier 1', 'EDC': 'Tier 4', ...}
    tier_lookup = {
        key.replace('_Tier', ''): value 
        for key, value in cas_tiers_dict.items() 
        if key.endswith('_Tier')
    }
    # --- END NEW ---

    # 3. Get All Evidence for the specific CASRN
    cas_evidence_df = evidence_df[evidence_df.CASRN == casrn].copy()
    if cas_evidence_df.empty:
         # Return error for evidence, but tiers are valid
        return {"error": f"CASRN '{casrn}' not found in the evidence log."}, tier_lookup

    # 4. --- FILTERING LOGIC ---
    # Map each evidence row's category to its final tier (e.g., 'CMR' -> 'Tier 1')
    cas_evidence_df['final_tier'] = cas_evidence_df['hazard_category'].apply(
        lambda cat: tier_lookup.get(cat) # Use new tier_lookup
    )

    # Filter the DataFrame: Keep only rows where the evidence's tier matches the final tier
    filtered_evidence_df = cas_evidence_df[
        cas_evidence_df['associated_tier'] == cas_evidence_df['final_tier']
    ].copy() # Use .copy() to avoid SettingWithCopyWarning
    
    if filtered_evidence_df.empty:
        # This is normal for Tier 4 (no evidence)
        return {}, tier_lookup # Return empty dict for evidence, but tiers are valid

    # 5. --- Proceed with original formatting logic ---
    
    civar_lookup = {
        'VH': 'Very High Hazard',
        'H': 'High Hazard',
        'M': 'Moderate Hazard',
        'L': 'Low Hazard',
        'I': 'Insufficient Data',
        'ND': 'No Data'
    }

    # Fill NaN in 'hazard_category_raw' to prevent groupby from dropping rows
    filtered_evidence_df['hazard_category_raw'] = filtered_evidence_df['hazard_category_raw'].fillna('')

    # Group the *filtered* data
    grouped = filtered_evidence_df.groupby(
        ['hazard_category', 'actual_value', 'value_type', 'hazard_category_raw']
    )['data_source'].apply(
        lambda x: '; '.join(sorted(list(set(x))))
    ).reset_index()

    output_dict = {}
    
    for row in grouped.itertuples():
        category = row.hazard_category
        value = row.actual_value
        v_type = row.value_type
        sources = row.data_source
        raw_category = row.hazard_category_raw 
        
        # Get the correct description and code to display
        if v_type == 'hcode':
            description = ghs_lookup.get(value, 'No GHS description')
            code_to_display = value
        elif v_type == 'civar_code':
            description = civar_lookup.get(value, 'No CIVAR description')
            code_to_display = raw_category
        else:
            description = 'Unknown value type'
            code_to_display = value
            
        # Format the evidence string with bold
        evidence_str = f"{code_to_display}: <b>{description}</b> ({sources})"
        
        if category not in output_dict:
            output_dict[category] = []
        output_dict[category].append(evidence_str)
        
    return output_dict, tier_lookup

# --- Main Execution Block (for independent testing) ---
if __name__ == "__main__":
    
    print("\n" + "="*50)
    print("--- Example Evidence Lookup ---")
    print("="*50)
    
    # Example: Formaldehyde (which should have lots of evidence)
    example_casrn = '50-00-0' 
    
    evidence = get_evidence_for_casrn(example_casrn)
    
    if 'error' in evidence:
        print(evidence['error'])
    else:
        print(f"Showing evidence for CASRN: {example_casrn}\n")
        # Use json.dumps for a clean print
        print(json.dumps(evidence, indent=2))

    print("\n" + "="*50)
    print("--- Example Evidence Lookup (No Data) ---")
    print("="*50)

    # Example: A CASRN with no data
    example_casrn_no_data = '123-45-6'
    evidence_no_data = get_evidence_for_casrn(example_casrn_no_data)
    print(f"Showing evidence for CASRN: {example_casrn_no_data}\n")
    print(json.dumps(evidence_no_data, indent=2))
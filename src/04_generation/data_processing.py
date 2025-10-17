# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 10:59:03 2025

@author: Gary
"""

# src/data_processing.py

import pandas as pd
import config  # Import the configuration

def load_and_prepare_data():
    """Loads all source data, merges them, and prepares the final dataframe."""
    
    # Load main fracfocus data
    # Note: I've assumed a filename for the main data. Adjust in config.py if needed.
    df = pd.read_parquet(
        config.FF_WORKING_DATA,
        columns=['bgCAS', 'epa_pref_name']
    )
    
    # Load tier classifications
    tiers = pd.read_parquet(config.TIERS_DATA_PQ)
    tiers = tiers.rename({'CASRN': 'bgCAS'}, axis=1)

    # Create helper columns for tier searching
    tiers['CMR_level'] = 'CMR' + tiers.CMR_Tier.str[-1]
    tiers['ENV_level'] = 'ENV' + tiers.ENV_Tier.str[-1]
    tiers['EDC_level'] = 'EDC' + tiers.EDC_Tier.str[-1]
    tiers['IHL_level'] = 'IHL' + tiers.IHL_Tier.str[-1]
    tiers['ORL_level'] = 'ORL' + tiers.ORL_Tier.str[-1]
    tiers['SKN_level'] = 'SKN' + tiers.SKN_Tier.str[-1]
    
    # Aggregate data by CAS number
    chem_summary = df.groupby('bgCAS', as_index=False)['epa_pref_name'].first()
    chem_summary = chem_summary.merge(tiers, on='bgCAS', how='left')
    
    # Create text for the searchable tier column
    def alttxt(row):
        return f'{row.CMR_level} {row.ENV_level} {row.EDC_level} {row.IHL_level} {row.ORL_level} {row.SKN_level}'
    chem_summary['alttxt'] = chem_summary.apply(alttxt, axis=1)
    
    print("Data loading and preparation complete.")
    return chem_summary

def get_ghs_codes():
    """Scrapes GHS codes from PubChem and returns them as a dictionary."""
    try:
        ghscodes_df = pd.read_html(config.GHS_CODES_URL)[0]
        ghscodes_df = ghscodes_df[['H-Code', 'Hazard Statements']].set_index('H-Code')
        ghs_dict = ghscodes_df.to_dict()['Hazard Statements']
        print("Successfully fetched GHS codes.")
        return ghs_dict
    except Exception as e:
        print(f"Could not fetch GHS codes: {e}")
        return {}
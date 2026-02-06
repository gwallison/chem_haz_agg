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
        config.MASTER_CAS_LIST,
        columns=['CASRN', 'orig_source']
    )
    df = df[~df.CASRN.isin(config.CAS_TO_IGNORE)]
    df = df.rename({'CASRN':'casrn'},axis=1)
    epadf = pd.read_parquet(config.EPA_CHEM_MASTER)
    epadf = epadf.rename({'preferredName':'chem_name'},axis=1)
    df = df.merge(epadf[['casrn','chem_name']],on='casrn',how='left')
    
    # Load tier classifications
    tiers = pd.read_parquet(config.TIERS_DATA_PQ)
    tiers = tiers.rename({'CASRN': 'casrn'}, axis=1)

    # Create helper columns for tier searching
    tiers['CMR_level'] = 'CMR' + tiers.CMR_Tier.str[-1]
    tiers['ENV_level'] = 'ENV' + tiers.ENV_Tier.str[-1]
    tiers['EDC_level'] = 'EDC' + tiers.EDC_Tier.str[-1]
    tiers['IHL_level'] = 'IHL' + tiers.IHL_Tier.str[-1]
    tiers['ORL_level'] = 'ORL' + tiers.ORL_Tier.str[-1]
    tiers['SKN_level'] = 'SKN' + tiers.SKN_Tier.str[-1]
    tiers['OGN_level'] = 'OGN' + tiers.OGN_Tier.str[-1]
    
    # prepare frames for search terms
    lofl = pd.read_parquet(config.LISTS_OF_LISTS_PROCESSED)
    list_def = pd.read_csv(config.LIST_OF_LISTS_DEFINED)
    
    concerns = list_def[list_def.list_type=='concern'].list_name.tolist()
    benign = list_def[list_def.list_type=='benign'].list_name.tolist()
    cgroups = list_def[list_def.list_type=='group'].list_name.tolist()
    
    # Aggregate data by CAS number
    chem_summary = df.groupby('casrn', as_index=False)[['chem_name','orig_source']].first()
    
    chem_summary = chem_summary.merge(tiers, on='casrn', how='left')
    # print(chem_summary.columns)
    # Create text for the searchable tier column
    def alttxt(row):
        return f'{row.CMR_level} {row.ENV_level} {row.EDC_level} {row.IHL_level} {row.ORL_level} {row.SKN_level} {row.OGN_level}'
    chem_summary['alttxt'] = chem_summary.apply(alttxt, axis=1)

    def concern_txt(row):
        t = lofl[lofl.CASRN==row.casrn][concerns].copy()
        # print(t)
        t['CASRN'] = row.casrn
        s = ''
        for col_name, col_data in t.items():
            if col_name=='CASRN':
                continue
            if col_data.any():
                s+= col_name + ' '
        return s   
    chem_summary['concerns'] = chem_summary.apply(concern_txt,axis=1)      
    
    def benign_txt(row):
        t = lofl[lofl.CASRN==row.casrn][benign].copy()
        # print(t)
        t['CASRN'] = row.casrn
        s = ''
        for col_name, col_data in t.items():
            if col_name=='CASRN':
                continue
            if col_data.any():
                s+= col_name + ' '
        return s   
    chem_summary['low_hazard'] = chem_summary.apply(benign_txt,axis=1)      
    
    def groups_txt(row):
        t = lofl[lofl.CASRN==row.casrn][cgroups].copy()
        # print(t)
        t['CASRN'] = row.casrn
        s = ''
        for col_name, col_data in t.items():
            if col_name=='CASRN':
                continue
            if col_data.any():
                s+= col_name + ' '
        return s   
    chem_summary['groups'] = chem_summary.apply(groups_txt,axis=1)    
    
    # print("Data loading and preparation complete.")
    # print(chem_summary.columns)
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
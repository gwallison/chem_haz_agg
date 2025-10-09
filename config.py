# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 09:50:34 2025

@author: Gary
"""

# config.py

import os

# --- Core Directories ---
# Use os.path.dirname(__file__) to make paths relative to this config file's location
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(PROJECT_ROOT,'mkdocs', 'docs')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RAW_DATA = os.path.join(DATA_DIR,'01_raw')
PROCESSED_DATA = os.path.join(DATA_DIR,'03_processed')

FF_REPO_DIR = r"G:\My Drive\production\repos\openFF_data_2025_09_07 - with watershed"
FF_WORKING_DATA = os.path.join(FF_REPO_DIR,'working_df.parquet')

# --- Input Data Paths ---
# This assumes your data files are in the 'data/' directory
# MAIN_DATA_PQ = os.path.join(DATA_DIR, 'main_disclosure_data.parquet') # Assuming a name for your main dataframe
TIERS_DATA_PQ = os.path.join(PROCESSED_DATA, 'final_tier_classifications.parquet')
GHS_DATA_PQ = os.path.join(PROCESSED_DATA, 'consolidated_GHS.parquet')
CHEMINFO_DATA_PQ = os.path.join(PROCESSED_DATA, 'cheminfo_hazard_summary.parquet')
ECHA_TEXT_DIR = os.path.join(RAW_DATA, 'by_casrn') # Directory for ECHA summary texts

COMPTOX_CASRN_DTXSID_MASTER = os.path.join(RAW_DATA,'comp_tox_casrn_dtxsid_master.csv')
EPA_CHEM_MASTER = os.path.join(PROCESSED_DATA,'epa_chem_master.parquet')

# --- Output Paths ---
HTML_TABLE_OUT = os.path.join(DOCS_DIR, 'assets', 'tables', 'my_table.html')
CHEMICAL_MD_OUT_DIR = os.path.join(DOCS_DIR, 'chemicals')

# --- Web URLs ---
GHS_CODES_URL = 'https://pubchem.ncbi.nlm.nih.gov/ghs/'
TIER_IMAGE_URL = 'https://storage.googleapis.com/open-ff-browser/images/ChemHazTier/{cas_num}.png'

# --- Table Settings ---
ITABLES_SETTINGS = {
    "columnDefs": [
        {"width": "75px", "targets": 0},
        {"width": "170px", "targets": 1},
        {"width": "160px", "targets": 2},
        {"visible": False, "targets": 3}
    ],
    "lengthMenu": [5, 10, 20, 50, 100],
    "pageLength": 5
}
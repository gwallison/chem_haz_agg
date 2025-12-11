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
INTERMED_DATA = os.path.join(DATA_DIR,'02_intermediate')
PROCESSED_DATA = os.path.join(DATA_DIR,'03_processed')

MASTER_CAS_LIST = os.path.join(PROCESSED_DATA,'master_cas_list.parquet')

FF_REPO_DIR = r"G:\My Drive\production\repos\openFF_data_2025_10_07"
FF_WORKING_DATA = os.path.join(FF_REPO_DIR,'working_df.parquet')



TSCA_RAW_CSV = os.path.join(RAW_DATA,'TSCAINV_052024.csv')
TEDX_RAW = os.path.join(RAW_DATA,'TEDX_EDC_trimmed.xls')
PROP65_RAW = os.path.join(RAW_DATA,'prop65_2025_01_03.csv')

# --- Input Data Paths ---
# This assumes your data files are in the 'data/' directory
# MAIN_DATA_PQ = os.path.join(DATA_DIR, 'main_disclosure_data.parquet') # Assuming a name for your main dataframe
TIERS_DATA_PQ = os.path.join(PROCESSED_DATA, 'final_tier_classifications.parquet')
GHS_DATA_PQ = os.path.join(PROCESSED_DATA, 'consolidated_GHS.parquet')
CHEMINFO_DATA_PQ = os.path.join(PROCESSED_DATA, 'cheminfo_hazard_summary.parquet')

RAW_CAS_DIR = os.path.join(RAW_DATA, 'by_casrn') # Directory for cas specific files, like scifinder
PROCESSED_CAS_DIR = os.path.join(PROCESSED_DATA, 'by_casrn') # Directory for cas specific files, like scifinder
ECHA_PAGES = os.path.join(RAW_DATA,'echa_pages')
ECHA_SUBSTANCE_LINKS = os.path.join(INTERMED_DATA,'echa_substance_links.parquet')

# NOT_USED_COMPTOX_CASRN_DTXSID_MASTER = os.path.join(RAW_DATA,'comp_tox_casrn_dtxsid_master.csv')


CHEMINFO_REF_DIR = os.path.join(RAW_DATA,'ChemInfo_ref_files')
EPA_CHEM_MASTER = os.path.join(PROCESSED_DATA,'epa_chem_master.parquet')
CASRN_DTXSID_MAP_OUTPUT = os.path.join(RAW_DATA,'epa_cas_dtxsid_map.parquet')
TEMP_CASRN_CSV = os.path.join(RAW_DATA,'temp_casrn_list.csv')

SCIFINDER_OUTPUT_PATH = os.path.join(PROCESSED_DATA,'scifinder_df.parquet')

# --- Output Paths ---
HTML_TABLE_OUT = os.path.join(DOCS_DIR, 'assets', 'tables', 'my_table.html')
# markdown chemical files
CHEMICAL_MD_OUT_DIR = os.path.join(DOCS_DIR, 'chemicals')

# GHS output files
PUBCHEM_OUTPUT_PATH = os.path.join(INTERMED_DATA,'pubchem_ghs_hazards.parquet')
CHEMINFO_GHS_OUTPUT_PATH = os.path.join(INTERMED_DATA,'cheminfo_ghs_hazards.parquet')
CHEMINFO_HAZARD_OUTPUT_PATH = os.path.join(INTERMED_DATA,'chem_infor_safety_data.parquet')
CHEMINFO_HAZARD_SUMMARY_PATH = os.path.join(INTERMED_DATA,'cheminfo_hazard_summary.parquet')
CHEMINFO_SDF_OUTPUT_PATH = os.path.join(INTERMED_DATA,'cheminfo_sdf_summary.parquet')

ECHA_HARM_OUTPUT_PATH= os.path.join(INTERMED_DATA,'echa_harmonized_ghs_hazards.parquet')
ECHA_INDUS_OUTPUT_PATH= os.path.join(INTERMED_DATA,'echa_industrial_ghs_hazards.parquet')

AUS_INPUT_XLSX = os.path.join(RAW_DATA,'HCResults.xlsx')
AUS_OUTPUT_PATH =os.path.join(INTERMED_DATA,'australia_ghs_hazards.parquet')

JAPAN_INPUT_XLSX = os.path.join(RAW_DATA,'list_nite_all_e.xlsx')
JAPAN_OUTPUT_PATH = os.path.join(INTERMED_DATA,'japan_ghs_hazards.parquet')

GHS_CONSOLIDATED_DATA_PATH = os.path.join(INTERMED_DATA,'consolidated_GHS.parquet')

GHS_CLASSIFICATION_OUTPUT_PATH = os.path.join(INTERMED_DATA, 
                                                 'GHS_hazard_classifications.parquet')
TIER_2_CLASSIFICATION_OUTPUT_PATH = os.path.join(INTERMED_DATA, 
                                                 'Tier_2_hazard_classifications.parquet')

FINAL_TIERED_OUTPUT_PATH = os.path.join(PROCESSED_DATA,
                                  'final_tier_classifications.parquet')
GHS_EVIDENCE_PATH = os.path.join(PROCESSED_DATA, 'ghs_evidence_log.parquet')

MASTER_EVIDENCE_LOG_PATH = os.path.join(PROCESSED_DATA,'master_evidence_log.parquet')

IRIS_EXCEL_FILE_PATH = os.path.join(RAW_DATA,'simple_list_alpha.xlsx')

## full list of EPA list membership; fetched manually, then processed
## see "List_oflists_section.py"
EPA_LISTS_OF_LISTS_RAW = os.path.join(RAW_DATA,'epa_lists.xlsx')


LISTS_OF_LISTS_PROCESSED = os.path.join(INTERMED_DATA,'list_of_lists_processed.parquet')
LIST_OF_LISTS_DEFINED = os.path.join(PROCESSED_DATA,'list_definitions.csv')
# --- Web URLs ---
GHS_CODES_URL = 'https://pubchem.ncbi.nlm.nih.gov/ghs/'

# This is the path for the PYTHON SCRIPT to FIND and READ the SVGs
TIER_IMAGE_DIR = '../mkdocs/docs/images'
TIER_IMAGE_URL = '../images/{cas_num}.svg'

# --- Hazard Details ----
HAZARD_MAP = {
    'CMR': {'1':['H350', 'H351', 'H340', 'H341', 'H360', 'H361', 'H362'
            'H350i','H360F','H360D','H360FD','H360Fd','H360Df','H361f',
            'H361d','H361fd'],
            '2': []},
    'ENV': {'1':['H400', 'H401','H410','H411'],
            '2':['H402','H412','H413','H420','H421']},
    'EDC': {'1':['H380', 'H381','H430','H431','H440', 'H441','H450','H451'],
            '2': []},
    'IHL': {'1':['H330','H331','H334','H300+H330','H310+H330','H300+H310+H330',
                 'H301+H311','H311+H331','H301+H311+H331','H304','H305'],
            '2':['H332','H333','H335','H336']},
    'ORL': {'1':['H301','H302','H300+H310','H300+H330','H300+H310+H330',
                 'H301+H311','H301+H311','H301+H311+H331','H304','H305'],
            '2':['H303']},
    'SKN': {'1':['H310','H311','H314','H318','H300+H310','H310+H330',
                 'H300+H310+H330','H301+H311','H311+H331','H301+H311+H331'],
            '2':['H312','H313','H315','H316','H317','H319','H320']},
    'OGN': {'1':['H370','H371','H372','H373'],
            '2':[]},
}

CHEMINFO_CATEGORY_MAP = {
    'CMR': ['Carcinogenicity', 'Genotoxicity_Mutagenicity', 'Reproductive', 'Developmental'],
    'ENV': ['Chronic_Aquatic_Toxicity', 'Acute_Aquatic_Toxicity'],
    'EDC': ['Endocrine_Disruption'],
    'IHL': ['Inhalation'],
    'ORL': ['Oral'],
    'SKN': ['Dermal','Skin_Irritation','Eye_Irritation','Skin_Sentization'],
    'OGN': []
}


# --- Table Settings ---
ITABLES_SETTINGS = {
    "columnDefs": [
        {"width": "75px", "targets": 0},
        {"width": "170px", "targets": 1},
        {"width": "160px", "targets": 2},
        {"width": "160px", "targets": 3},
        {"visible": False, "targets": 4}
    ],
    "lengthMenu": [5, 10, 20, 50, 100],
    "pageLength": 5
}
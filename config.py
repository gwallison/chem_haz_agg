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
OPENFF_BUILD_NEW_CAS = r"C:\MyDocs\integrated\openFF\build\sandbox\work_dir\new_cas_added.parquet"
MOLECULE_PIC_DIR = r"C:\MyDocs\integrated\openFF\images\pic_dir"



TSCA_RAW_CSV = os.path.join(RAW_DATA,'TSCAINV_072025.csv')
TEDX_RAW = os.path.join(RAW_DATA,'TEDX_EDC_trimmed.xls')
PROP65_RAW = os.path.join(RAW_DATA,'prop65_2025_12_05.csv')

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
ECHA_SELF_CLASSIFIED_PATH = os.path.join(INTERMED_DATA,'echa_self_classifications.parquet')
ECHA_SELF_SUMMARY_PATH = os.path.join(INTERMED_DATA,'echa_self_summary.parquet')

# NOT_USED_COMPTOX_CASRN_DTXSID_MASTER = os.path.join(RAW_DATA,'comp_tox_casrn_dtxsid_master.csv')


CHEMINFO_REF_DIR = os.path.join(RAW_DATA,'ChemInfo_ref_files')
EPA_CHEM_MASTER = os.path.join(PROCESSED_DATA,'epa_chem_master.parquet')
CASRN_DTXSID_MAP_OUTPUT = os.path.join(RAW_DATA,'epa_cas_dtxsid_map.parquet')
TEMP_CASRN_CSV = os.path.join(RAW_DATA,'temp_casrn_list.csv')
QUARANTINE_CASRN_CSV = os.path.join(PROCESSED_DATA,'master_cas_list_quarantine.csv')
REMOVED_CASRN_LOG = os.path.join(PROCESSED_DATA,'master_cas_list_removed.csv')
MASTER_CAS_LIST_BACKUP_DIR = os.path.join(PROCESSED_DATA,'backups')
EPA_HAZ_TOXVAL_JSON_DIR = os.path.join(RAW_DATA,'epa_haz_toxval_json')
EPA_CHEM_API_JSON_DIR = os.path.join(RAW_DATA,'epa_chem_api_json')

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
IRIS_PROCESSED = os.path.join(INTERMED_DATA,"iris_data.parquet")
PPRTV_EXCEL_FILE_PATH = os.path.join(RAW_DATA,'pprtv_chemicals.xls')
PPRTV_PROCESSED = os.path.join(INTERMED_DATA,"pprtv_data.parquet")
NJ_RTK_DATASHEET_PATH = os.path.join(INTERMED_DATA,"nj_hazardous_substances.parquet")
ATSDR_OUTPUT_PATH = os.path.join(INTERMED_DATA,'atsdr_casrn.parquet')
NIOSH_POCKET_PATH = os.path.join(INTERMED_DATA,'niosh_pocket_datasheets.parquet')
CAMEO_RAW = os.path.join(RAW_DATA,"cameo_links_master_v3.csv")
CAMEO_PROCESSED = os.path.join(INTERMED_DATA,'cameo_datasheets.parquet')
OECD_CHEMICALS = os.path.join(INTERMED_DATA,'oecd_chem.parquet')
OECD_GROUPS = os.path.join(INTERMED_DATA,'oecd_groups.parquet')
OECD_CHEMICAL_DETAILS = os.path.join(INTERMED_DATA,'oecd_chem_details.parquet')
RAW_GRAS_DETAILS = os.path.join(RAW_DATA, 'raw_gras_chem.csv')
GRAS_DETAILS = os.path.join(INTERMED_DATA, 'gras_chem.parquet')

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
# to be a level 1 hazard here, the hcode must be a Category 1 or 2.
# A level 2 hazard will be a Category 3, 4 or 5 hcode.
# using pubchem chart: https://pubchem.ncbi.nlm.nih.gov/ghs/

# Replaced 4/14/2026
# HAZARD_MAP = {
#     'CMR': {'1':['H350', 'H351', 'H340', 'H341', 'H360', 'H361', 'H362'
#             'H350i','H360F','H360D','H360FD','H360Fd','H360Df','H361f',
#             'H361d','H361fd'],
#             '2': []},
#     'ENV': {'1':['H400', 'H401','H410','H411'],
#             '2':['H402','H412','H413','H420','H421']},
#     'EDC': {'1':['H380', 'H381','H430','H431','H440', 'H441','H450','H451'],
#             '2': []},
#     'IHL': {'1':['H330','H331','H334','H300+H330','H310+H330','H300+H310+H330',
#                  'H301+H311','H311+H331','H301+H311+H331','H304','H305'],
#             '2':['H332','H333','H335','H336']},
#     'ORL': {'1':['H300','H301','H300+H310','H300+H330','H300+H310+H330',
#                  'H301+H311','H301+H311','H301+H311+H331','H304','H305'],
#             '2':['H303','H302','H302+H312']},
#     'SKN': {'1':['H310','H311','H314','H315','H317','H318','H319','H320','H300+H310','H310+H330',
#                  'H300+H310+H330','H301+H311','H311+H331','H301+H311+H331'],
#             '2':['H312','H313','H316','H302+H312']},
#     'OGN': {'1':['H370','H371','H372','H373'],
#             '2':[]},
# }

HAZARD_MAP = {
    'CMR': {
        '1': ['H340', 'H341', 'H350', 'H350i', 'H351', 'H360', 'H360F', 'H360D',
              'H360FD', 'H360Fd', 'H360Df', 'H361', 'H361f', 'H361d', 'H361fd', 'H362'],
        '2': []
    },
    'ENV': {
        '1': ['H400', 'H401', 'H410', 'H411', 'H420', 'H421'],
        '2': ['H402', 'H412', 'H413']
    },
    # not strictly in the PubChem version.  To be used by ECHA.
    'EDC': {
        '1': ['H380', 'H381','H430','H431','H440', 'H441','H450','H451'],
        '2': []
    },
    'IHL': {
        '1': ['H330', 'H331', 'H334', 'H304', 'H305',
              'H300+H330', 'H310+H330', 'H300+H310+H330',
              'H301+H331', 'H311+H331', 'H301+H311+H331'],
        '2': ['H332', 'H333', 'H335', 'H336']
    },
    'ORL': {
        '1': ['H300', 'H301', 'H304', 'H305',
              'H300+H310', 'H300+H330', 'H300+H310+H330',
              'H301+H311', 'H301+H331', 'H301+H311+H331'],
        '2': ['H302', 'H303',
              'H302+H312', 'H302+H332', 'H302+H312+H332',
              'H303+H313', 'H303+H333', 'H303+H313+H333']
    },
    'SKN': {
        '1': ['H310', 'H311', 'H314', 'H315', 'H317', 'H318', 'H319', 'H320',
              'H300+H310', 'H310+H330', 'H300+H310+H330',
              'H301+H311', 'H311+H331', 'H301+H311+H331',
              'H315+319', 'H315+H320'],
        '2': ['H312', 'H313', 'H316',
              'H302+H312', 'H312+H332', 'H302+H312+H332',
              'H303+H313', 'H313+H333', 'H303+H313+H333']
    },
    'OGN': {
        '1': ['H370', 'H371', 'H372', 'H373'],
        '2': []
    },
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
# Some materials are not valid in the GHS world, but still have
#   data; they should not be in our catalog.
# Other non-valid CASRN, such as are used in Open-FF, should also be ignored.

CAS_TO_IGNORE = ['proprietary','ambiguousID','conflictingID', #Open-FF metalabels
                 '7732-18-5', # water
                 '7727-37-9', # N2
                 '124-38-9',  # CO2
                 ]

# --- Table Settings ---
ITABLES_SETTINGS = {
    "columnDefs": [
        {"width": "75px", "targets": 0},
        {"width": "200px", "targets": 1},
        {"width": "60px", "targets": 2},
        {"width": "80px", "targets": 3},
        {"width": "80px", "targets": 4},
        {"width": "80px", "targets": 5},
        {"visible": False, "targets": 6}, # tier code
        {"visible": False, "targets": 7}, # data source

    ],
    "lengthMenu": [5, 10, 20, 50, 100],
    "pageLength": 5
}
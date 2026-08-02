# -*- coding: utf-8 -*-
"""
Created on Tue Sep  9 19:56:18 2025

@author: Gary
"""
import pandas as pd
import os
import sys

# Add the project root to the Python path to resolve the 'config' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config import PUBCHEM_OUTPUT_PATH, CHEMINFO_GHS_OUTPUT_PATH
from config import ECHA_HARM_OUTPUT_PATH, ECHA_INDUS_OUTPUT_PATH
from config import AUS_OUTPUT_PATH, JAPAN_OUTPUT_PATH
from config import GHS_CONSOLIDATED_DATA_PATH

outdir = r"C:\MyDocs\integrated\chem_profiles\code\data"

def create_consolidated_GHS():
    pchem = pd.read_parquet(PUBCHEM_OUTPUT_PATH)
    pchem['source'] = 'PubChem'
    
    chemi = pd.read_parquet(CHEMINFO_GHS_OUTPUT_PATH)
    chemi['source'] = 'ChemInformatics'
    
    echa_harm = pd.read_parquet(ECHA_HARM_OUTPUT_PATH)
    echa_harm['source'] = 'ECHA Harmonized'
    
    aus = pd.read_parquet(AUS_OUTPUT_PATH)
    aus['source'] = 'Australia'
    
    japan = pd.read_parquet(JAPAN_OUTPUT_PATH)
    japan['source'] = 'Japan'
    
    echa_indus = pd.read_parquet(ECHA_INDUS_OUTPUT_PATH)
    echa_indus['source'] = 'ECHA self-classified industry'
    
    alldf = pd.concat([pchem,
                       chemi,
                       echa_harm,
                       aus,
                       japan,
                       echa_indus])
    alldf.to_parquet(GHS_CONSOLIDATED_DATA_PATH)
    return alldf

if __name__ == '__main__':
    create_consolidated_GHS()
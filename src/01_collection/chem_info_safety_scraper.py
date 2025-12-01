# -*- coding: utf-8 -*-
"""
Created on Tue Nov 18 18:44:50 2025

@author: Gary
"""
import pandas as pd
import os
import config
import numpy as np

ref_dir = config.CHEMINFO_REF_DIR

# def tolst(s):
#     try:
#         return s.split(',')
#     except:
#         return []

def construct_df_from_safety_file(fn):
    date = fn[7:17]
    t = pd.read_excel(os.path.join(ref_dir,fn),header=1)
    out = t[['CASRN','GHS Codes','Signal']].copy()
    out['GHS_Signals'] = out.Signal
    out['GHS_Pictograms'] ='N/A'
    out['GHS_P_Codes'] = 'N/A'
    # out['GHS_H_Codes'] = out['GHS Codes'].map(lambda x: tolst(x))
    out['GHS_H_Codes'] = out['GHS Codes'] # takes a string, not list
    out['Download_Date'] = date
    return out[['CASRN','GHS_H_Codes','GHS_Signals',
                'GHS_Pictograms','GHS_P_Codes',
                'Download_Date']]
    
def make_full_set():
    alldf = []
    ldir = os.listdir(ref_dir)
    for fn in ldir:
        if fn[:6] == 'safety':
            alldf.append(construct_df_from_safety_file(fn))
    
    final = pd.concat(alldf)
    print(f'Total number cas: {len(final)}')
    final.to_parquet(config.CHEMINFO_GHS_OUTPUT_PATH)

if __name__ == '__main__':
    make_full_set()            

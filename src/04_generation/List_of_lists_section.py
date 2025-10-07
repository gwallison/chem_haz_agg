# -*- coding: utf-8 -*-
"""
Created on Sat Oct  4 15:27:02 2025

@author: Gary

This is used to generate the different text sections of the
chemical page's dealing with the membership to lists of concern,
such as the CWA list, etc.
"""

import pandas as pd

class List_of_list():
    
    def __init__(self):
        self.lldf = pd.read_parquet(r'C:/MyDocs/integrated/chem_profiles/data/02_intermediate/list_of_lists.parquet')
        self.lldf = self.lldf.reset_index()
        self.lists_of_concern = ['CleanWaterAct','Prop65','TEDX']
        # print(self.lldf.head())
        

    def get_list_of_concerns(self,cas):
        """simply returns the names of the lists of concerns
        the given chemical is on"""
        t = self.lldf[self.lldf.CASRN==cas][self.lists_of_concern]
        try:
            true_columns = t.columns[t.iloc[0] == True].tolist()
            # print(f'{cas}: {true_columns}')
            return true_columns
        except: # empty list
            return []
        
    def get_concerns_grid(self,cas):
        """return a string with grid of concern lists"""
        lst = self.get_list_of_concerns(cas)
        if len(lst)>0:
            s = '## Membership on Lists of Concern\n\n'
            s += '<div class="grid cards" markdown> \n\n'
            
            for name in lst:
                s+= f'-   :smile: **{name}**\n\n'
                s+= '    ---\n\n'
                s+= f'    Description of {name}\n\n'
            s+='</div>'
            return s
        return ''
        
        
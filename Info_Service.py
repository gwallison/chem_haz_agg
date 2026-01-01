# -*- coding: utf-8 -*-
"""
Created on Mon Oct 27 11:46:21 2025

@author: Gary
"""
import sys
sys.path.insert(0,'c:/MyDocs/integrated/') # adjust to your setup

import pandas as pd
import chem_profiles.config as config
import re

class Info_Service():
    def __init__(self):
        # set up empty frames.  Only loaded if used.
        self.epa_master = pd.DataFrame()
        self.scifinder_info = pd.DataFrame()     
        self.tier_summary = pd.DataFrame()
        self.tsca_df = pd.DataFrame()
        self.list_of_lists = pd.DataFrame()

        
    # -------------------   TIERS values  -----------------
    def _load_tier(self):
        if self.tier_summary.empty:
            self.tier_summary= pd.read_parquet(config.TIERS_DATA_PQ).set_index('CASRN')
        return self.tier_summary

    def get_tier_list(self,cas):
        """
        Retrieves a formatted list of tier information for a given CASRN.
    
        The function looks for columns ending in '_Tier', extracts the prefix (YYY)
        from the column name and the digit (X) from the cell value ('Tier X'),
        and combines them into a list of strings ('YYYX').
    
        Args:
            casrn (str): The CASRN index value to look up.
            dataframe (pd.DataFrame): The DataFrame (indexed by CASRN) to search.
    
        Returns:
            list: A list of strings in the format "YYYX", e.g., ["ABC2", "DEF1"].
                  Returns an empty list if the CASRN is not found or has no valid
                  tier entries.
        """
        df = self._load_tier()
        try:
            # 1. Select the row for the given CASRN
            row = df.loc[cas]
    
            # 2. Filter this row (which is a Series) to get only 'Tier' columns
            tier_series = row[row.index.str.endswith('_Tier')]
    
            # 3. Drop any rows with missing (NaN) or invalid data
            # This ensures we only process cells that actually contain 'Tier X'
            valid_tiers = tier_series.dropna()
            valid_tiers = valid_tiers[valid_tiers.str.startswith('Tier ')]
    
            if valid_tiers.empty:
                return []
    
            # 4. Extract the 'YYY' part from the column name (the Series index)
            # e.g., 'ABC_Tier' -> 'ABC'
            col_prefixes = valid_tiers.index.str.removesuffix('_Tier')
    
            # 5. Extract the 'X' part from the cell value
            # e.g., 'Tier 2' -> '2' (takes the last character)
            tier_numbers = valid_tiers.str[-1]
    
            # 6. Combine the prefixes and numbers and return as a list
            # This works element-wise because both are Series with the same index
            combined_list = (col_prefixes + tier_numbers).tolist()
    
            return combined_list
    
        except KeyError:
            # Handle the case where the CASRN is not in the DataFrame's index
            print(f"Warning: CASRN '{cas}' not found in DataFrame.")
            return []
        except Exception as e:
            # Handle other potential errors (e.g., data not in string format)
            print(f"An error occurred processing {cas}: {e}")
            return []

    # def get_tiers_summary_list(self,cas):
    #     df = self._load_tier()

    #     try:
    #         return df.loc[cas,'preferredName']
    #     except:
    #         return 'no epa preferred name'
    
    
    # --------------------  List of lists ----------------
    def _load_list_of_lists(self):
        if self.list_of_lists.empty:
            self.list_of_lists = pd.read_parquet(config.LISTS_OF_LISTS_PROCESSED)
        return self.list_of_lists
    
    def get_list_of_concerns(self,cas):
        pass
    # --------------------   EPA STUFF --------------------        
    def _load_epa(self):
        if self.epa_master.empty:
            self.epa_master = pd.read_parquet(config.EPA_CHEM_MASTER).set_index('casrn')
        return self.epa_master

    def get_epa_pref_name(self,cas):
        df = self._load_epa()
        try:
            return df.loc[cas,'preferredName']
        except:
            return 'no epa preferred name'
        
    # --------------------   SciFinder Stuff ---------------
    def _load_scifinder(self):
        if self.scifinder_info.empty:
            self.scifinder_info = pd.read_parquet(config.SCIFINDER_OUTPUT_PATH).set_index('CASRN') 
        return self.scifinder_info


    def get_scifinder_name(self,cas,remove_scifi_suffix=True):
        # 
        pattern = r'\s+\([^)]*[A\d]CI[^)]*\)$'
        df = self._load_scifinder()
        try:
            s = df.loc[cas,'sf_name']
            print(s)
            if remove_scifi_suffix:
                s = re.sub(pattern, '', s)
            return s
        except:
            return 'no scifinder name'

    def get_scifinder_molecule(self,cas):
        df = self._load_scifinder()
        try:
            s = df.loc[cas,'mole_form']
            return s
        except:
            return 'no scifinder mole_form'
        
    def get_scifinder_substance_class(self,cas):
        df = self._load_scifinder()
        try:
            lst = df.loc[cas,'subs_class']
            s = ''
            for item in lst:
                s+= item+'; '
            return s[:-2]
        except:
            return 'no scifinder substance_class'
    
    def get_scifinder_components_as_list(self,cas):
        df = self._load_scifinder()
        try:
            lst1 = list(df.loc[cas,'comp1'])
            lst2 = list(df.loc[cas,'comp2'])
            return lst1+lst2
        except:
            print('error in fetching components as list')
            return []

    def get_scifinder_numref(self,cas):
        df = self._load_scifinder()
        try:
            svalue = df.loc[cas,'numref']
            # print(f'numref 1: {svalue}')
            svalue = svalue.replace(',','')
            if 'K' in svalue:
                t = svalue.replace('K','')
                t = int(t)*1000
                return t
            if 'M' in svalue:
                t = svalue.replace('M','')
                t = int(t)*1000000
                return t
            return int(svalue)
                
        except:
            print('except numref')
            return 'number references not valid'
    
    def is_on_list(self,cas,list_name):
        # fetch list
        df = self._load_list_of_lists()
        try:
            val = df[df.CASRN==cas][list_name].tolist()[0]
            # print(val)
            return val 
        except:
            return False
    


if __name__ == '__main__':
    infosrv = Info_Service()
    print(infosrv.get_epa_pref_name(cas='50-00-0'))
    print(infosrv.get_tier_list(cas='50-00-0'))
    print(infosrv.is_on_list(cas='50-00-0', list_name='is_UVCB'))
    print(infosrv.get_scifinder_components_as_list(cas='10025-69-1'))
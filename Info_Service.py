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
        self.epa_master = pd.read_parquet(config.EPA_CHEM_MASTER).set_index('casrn')
        self.scifinder_info = pd.DataFrame()     
        self.tier_summary = pd.read_parquet(config.TIERS_DATA_PQ).set_index('CASRN')
        self.tsca_df = pd.DataFrame()
        
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
            lst1 = df.loc[cas,'comp1']
            lst2 = df.loc[cas,'comp2']
            print(lst1)
            print(lst2)
            return 'not working yet'
        except:
            print('errror')
            return []
    
    #-------------------  Other data sets --------------------
    def _load_tsca(self):
        if self.tsca_df.empty:
            self.tsca_df = pd.read_csv(config.TSCA_RAW_CSV,
                                       usecols=['CASRN','UVCB']) #'FLAG','ACTIVITY'])
            self.tsca_df = self.tsca_df.set_index('CASRN')
        return self.tsca_df
    
    def is_UVCB(self,cas):
        df = self._load_tsca()
        try:
            val = df.loc[cas,'UVCB']
            if val == 'UVCB':
                return True
            return False
        except:
            return False

    def is_non_TSCA(self,cas):
        df = self._load_tsca()
        df = df.reset_index()
        if cas in df.CASRN.tolist():
            return False
        return True


if __name__ == '__main__':
    infosrv = Info_Service()
    print(infosrv.is_UVCB(cas='64742-47-8'))
    print(infosrv.is_UVCB(cas='50-00-0'))
    print(infosrv.is_non_TSCA(cas='50-00-0'))
    print(infosrv.is_UVCB(cas='64742-47-8'))    
    print(infosrv.get_scifinder_substance_class(cas='50-00-0'))
    print(infosrv.get_epa_pref_name(cas='50-00-0'))
    print(infosrv.get_tier_list(cas='50-00-0'))
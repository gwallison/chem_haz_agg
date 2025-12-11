# -*- coding: utf-8 -*-
"""
Created on Sat Oct  4 15:27:02 2025

@author: Gary

This is used to generate the different text sections of the
chemical page's dealing with the membership to lists of concern,
such as the CWA list, etc.
"""

import pandas as pd
# import numpy as np
from typing import Dict, List, Set, Union

import config


class List_of_list():
    
    def __init__(self):
        
        self.list_definitions = pd.read_csv(config.LIST_OF_LISTS_DEFINED)
        self.list_dict = {}
        for i,row in self.list_definitions.iterrows():
            self.list_dict[row.list_name] ={
                'alias':row.list_alias,
                'link':row.source_link,
                'source':row.source,
                'type':row.list_type, #'concern','benign','group'
                'annon':row.annotation}
        self.concern_lists = self.list_definitions[self.list_definitions.list_type=='concern'].list_name.tolist()
                    
        # self.list_def = self.list_def.set_index('list_name')
        # self.concern_lists = self.list_def.to_dict()
        
        # self.concern_lists = {'is_on_Prop65':('Calif. Prop 65',
        #                                       'https://oehha.ca.gov/proposition-65'),
        #                       'is_on_TEDX':('TEDX list',
        #                                     'https://endocrinedisruption.org/interactive-tools/endocrine-basics'),
        #                       'CWA311HS':('Clean Water Act',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/CWA311HS'),
        #                       'CCL':('Safe Drinking Water Act',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/CCL'),
        #                       'PFAS8a7':('EPA PFAS 2024 list',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/PFAS8a7'),
        #                       'AEGLVALUES':('Acute Exposure Guidelines',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/AEGLVALUES'),
        #                       'EPAHAPS':('Hazardous Air Pollutants',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/EPAHAPS'),
        #                       'NATADB':('National Air Toxics Assessment',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/NATADB'),
        #                       'IARC1':('IARC Carcinogens (group 1)',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/IARC1'),
        #                       'IARC2A':('IARC Carcinogens (group 2A)',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/IARC2A'),
        #                       'IARC2B':('IARC Carcinogens (group 2B)',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/IARC2B'),
        #                       'NERVEAGENTS':('Nerve Agents',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/NERVEAGENTS'),
        #                       'PESTACTIVES':('Pesticide Active Ingredients',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/PESTACTIVES'),
        #                       'SINLIST': ('"Substitute In Now" list',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/SINLIST'),
        #                       'STOCKHOLM': ('Persistant Organic Polluntants',
        #                                   'https://comptox.epa.gov/dashboard/chemical-lists/STOCKHOLM'),
        #                       }

        self.epa_group_lists = {'PAHLIST':'Polycyclic Aromatics (PAHs)',
                                 }
        self.df_of_lists = pd.read_parquet(config.LISTS_OF_LISTS_PROCESSED)


    def incorporate_casrn_lists(
        self,
        # master_df: pd.DataFrame, 
        source_lists: Dict[str, Union[List[str], Set[str]]], 
        casrn_col_name: str = 'CASRN'
    ) -> pd.DataFrame:
        """
        Creates a master DataFrame with boolean columns indicating if the CASRN
        from the master list is present in various source lists.
    
        Args:
            source_lists: A dictionary where keys are the names of the sources 
                          (for the new columns) and values are the lists or sets 
                          of CASRNs from those sources.
            casrn_col_name: The name of the column in master_df containing the CASRNs.
                            Defaults to 'CASRN'.
    
        Returns:
            The updated master DataFrame with new boolean columns.
        """
        # Create a copy to avoid modifying the original DataFrame
        result_df =  pd.read_parquet(config.MASTER_CAS_LIST)[['CASRN']].copy()
              
        # 💡 Optimization: Convert lists to sets for O(1) average time complexity 
        # lookups, which is much faster than O(n) for lists, especially with large datasets.
        source_sets = {
            name: set(cas_list) if not isinstance(cas_list, set) else cas_list
            for name, cas_list in source_lists.items()
        }
        
        # Iterate through the source sets and apply the isin() method
        for source_name, cas_set in source_sets.items():
            # The isin() method returns a boolean Series indicating whether each 
            # element in the master CASRN column is contained in the source_set.
            new_col_name = f'{source_name}'
            result_df[new_col_name] = result_df[casrn_col_name].isin(cas_set)
            
        return result_df
    
    def _get_epa_lists(self,sources):
        print('  -- get EPA lists')
        cond = self.list_definitions.source=='EPA'
        cols = self.list_definitions[cond].list_name.tolist()
        # gcols = list(self.epa_group_lists.keys())
        # ccols = list(self.epa_concern_lists.keys())

        indf = pd.read_excel(config.EPA_LISTS_OF_LISTS_RAW,
                             # usecols=ccols+gcols+['INPUT'],
                             usecols=cols+['INPUT'],
                             sheet_name=1)
        indf = indf.rename({'INPUT':'CASRN'},axis=1)
        # indf = indf.set_index('CASRN')
        
        # check if source_name already used
        sources_names = list(sources.keys())
        for col in cols:
            if col in sources_names:
                print(f'!!! {col} name already used !!!  OVERWRITING!')
            caslst = indf[indf[col]=='Y'].CASRN.tolist()
            sources[col] = caslst
        return sources

    
    def _get_tsca_lists(self,sources):
        print('  -- get TSCA lists')
        t = pd.read_csv(config.TSCA_RAW_CSV, 
                        usecols=['CASRN','UVCB'])

        sources_names = list(sources.keys())
        for col in ['is_UVCB','is_on_TSCA']:
            if col in sources_names:
                print(f'!!! {col} name already used !!!  OVERWRITING!')

        sources['is_UVCB'] = t[t.UVCB=='UVCB'].CASRN.tolist()
        sources['is_on_TSCA'] = t.CASRN.tolist()

        return sources
    
    def _get_tedx_lists(self,sources):
        print('  -- get TEDX list')
        t = pd.read_excel(config.TEDX_RAW, 
                        usecols=['CASRN'])

        sources_names = list(sources.keys())
        for col in ['is_on_TEDX']:
            if col in sources_names:
                print(f'!!! {col} name already used !!!  OVERWRITING!')

        sources['is_on_TEDX'] = t.CASRN.tolist()

        return sources
        
    def _get_prop56_lists(self,sources):
        print('  -- get PROP65 list')
        t = pd.read_csv(config.PROP65_RAW, 
                        usecols=['CAS No.'])
        t['CASRN'] = t['CAS No.']
        sources_names = list(sources.keys())
        for col in ['is_on_Prop65']:
            if col in sources_names:
                print(f'!!! {col} name already used !!!  OVERWRITING!')

        sources['is_on_Prop65'] = t.CASRN.tolist()

        return sources
    
    def remake_all_lists(self):
        # create the list of lists from scratch using the RAW file
        # That dataframe has only the master_cas_list items, but
        #  booleans for every column.
        print('\n*** Recreating the List of lists frame ***\n')
        sources = {}
        
        sources = self._get_epa_lists(sources)
        sources = self._get_tsca_lists(sources)
        sources = self._get_tedx_lists(sources)
        sources = self._get_prop56_lists(sources)
        
        out = self.incorporate_casrn_lists(sources)   
        out.to_parquet(config.LISTS_OF_LISTS_PROCESSED)
        # print(out.head())             
        
        
    # def get_list_of_groups(self,cas):
    #     """returns markdown of the lists of groups
    #     the given chemical is on"""
    #     # t = self.lldf[self.lldf.CASRN==cas][self.lists_of_concern]
    #     out = ''
        
    #     # EPA
    #     t = self.epa_processed_df[self.epa_processed_df.CASRN==cas]
    #     gcols = list(self.epa_group_lists.keys())

    #     t = t[gcols+['CASRN']]
    #     try:
    #         true_columns = t.columns[t.iloc[0] == True].tolist()
    #         for item in true_columns:
    #             out+= f'    [{self.epa_concern_lists[item]}](https://comptox.epa.gov/dashboard/chemical-lists/{item})\n\n'            
    #     except: # empty list
    #         pass
        
    #     # TSCA
        
    #     t = self.tsca_processed_df[self.tsca_processed_df.CASRN==cas]
    #     gcols = ['UVCB','on_TSCA']

    #     t = t[gcols+['CASRN']]
    #     try:
    #         true_columns = t.columns[t.iloc[0] == True].tolist()
    #         if 'UVCB' in true_columns:
    #             out+= '    [Unknown, variable, or reaction compound](https://www.epa.gov/sites/default/files/2015-05/documents/uvcb.pdf)\n\n'            
    #         if 'on_TSCA' in true_columns:
    #             out+= '    [On TSCA list](https://www.epa.gov/laws-regulations/summary-toxic-substances-control-act)\n\n'            
    #     except: # empty list
    #         pass
        
    #     return out
    

    # def get_list_of_concerns(self,cas):
    #     """returns markdown of the lists of concerns
    #     the given chemical is on"""

    #     out = ''
    #     d = self.list_dict

    #     t = self.df_of_lists[self.df_of_lists.CASRN==cas]
    #     ccols = self.concern_lists

    #     t = t[ccols+['CASRN']]
    #     try:
    #         true_columns = t.columns[t.iloc[0] == True].tolist()
    #         for name in true_columns:
    #             # out+= f'    [{self.concern_lists[item][0]}]({self.concern_lists[item][1]})\n\n'            
    #             # out+= f'    [{d[name]["alias"]}]({d[name]["link"]})\n\n'            
    #             out+= f'    <a href="{d[name]["link"]}" target="_blank">{d[name]["alias"]}</a>\n\n'
    #     except: # empty list
    #         pass
    #     return out

    def get_markdown_list_by_type(self,cas,ltype='concern'):
        """returns markdown of the lists of 
        the given chemical is on"""

        out = ''
        d = self.list_dict

        t = self.df_of_lists[self.df_of_lists.CASRN==cas]
        cols = self.list_definitions[self.list_definitions.list_type==ltype].list_name.tolist()
        # ccols = self.concern_lists

        t = t[cols+['CASRN']]
        try:
            true_columns = t.columns[t.iloc[0] == True].tolist()
            if len(true_columns)>0:
                # annot = ''
                for i,name in enumerate(true_columns):
                    out+= f'    **{d[name]["alias"]}** {d[name]["annon"]} [Link]({d[name]["link"]}) \n\n'
        except: # empty list
            pass
        return out

    def get_simple_list(self,cas):
        out = ''

        t = self.df_of_lists[self.df_of_lists.CASRN==cas]
        cols = self.list_definitions.list_name.tolist()

        t = t[cols+['CASRN']]
        out = []
        try:
            out = t.columns[t.iloc[0] == True].tolist()
        except: # empty list
            print('something wrong with get_simple_list')
        return out
        

    # def get_concerns_grid(self,cas):
    #     """return a string with grid of concern lists"""
    #     lst = self.get_list_of_concerns(cas)
    #     if len(lst)>0:
    #         s = '## Membership on Lists of Concern\n\n'
    #         s += '<div class="grid cards" markdown> \n\n'
            
    #         for name in lst:
    #             s+= f'-   :smile: **{name}**\n\n'
    #             s+= '    ---\n\n'
    #             s+= f'    Description of {name}\n\n'
    #         s+='</div>'
    #         return s
    #     return ''
        
    
def remake_raw_lists():
    ll = List_of_list()
    ll.remake_all_lists()
    
if __name__ == '__main__':
    remake_raw_lists()
    # ll = List_of_list()
    # # df = pd.DataFrame(ll.concern_lists).reset_index().T
    # # df.to_csv(config.LIST_OF_LISTS_DEFINED)    
    # print(ll.concern_lists)
# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 10:59:55 2025

@author: Gary
"""

# src/page_generators.py

import os
import pandas as pd
import itables
import config # Import the configuration
import data_processing as dp
import chem_page_header as cph
import List_of_lists_section as lols
import Info_Service as ifs

infosrv = ifs.Info_Service()

# import make_graphics

from itables import init_notebook_mode
init_notebook_mode(all_interactive=True, connected=True)
# from itables import show as iShow
import itables.options as opt
opt.classes="display compact cell-border"
opt.buttons=['pageLength', "copyHtml5", "csvHtml5", ]
opt.maxBytes = 0
opt.allow_html = True

outsize = None # set to None for full run


def getProlog():
    s = """
### FAQ
??? info "Click to read..."
    __What is the Chemical Hazard Information Aggregator?__
    
    The Chemical Hazard Information Aggregator is a specialized data tool designed to centralize and harmonize complex toxicological information. By pulling from diverse sources—such as the EPA, ECHA, and international GHS databases—it provides a single, searchable interface for understanding the intrinsic properties of chemicals used in industrial processes. This platform eliminates the need to manually cross-reference multiple disparate registries, allowing users to quickly identify high-priority chemicals like PFAS or those with specific GHS classifications.
    
    __How does "hazard" differ from "risk"?__
    
    Understanding the distinction between these two terms is fundamental to chemical safety and regulatory analysis:

    * **Hazard** refers to the inherent property of a substance that makes it capable of causing harm. For example, a chemical may be "hazardous" because it is toxic to aquatic life, flammable, or carcinogenic. This status does not change based on how the chemical is used.

    * **Risk** is the likelihood that harm will occur from **exposure** to that hazard. Risk is a function of both the hazard and the exposure (Risk = Hazard × Exposure).

    In short: A shark in the ocean is a hazard. If you stay on the beach, the risk is low. If you go for a swim, the risk increases, even though the shark’s "hazard" level remains the same.  __This website can only provide information about Hazard.__
    
    __Where does the data on this site come from?__
    
    The aggregator compiles data from authoritative national and international bodies. This includes GHS (Globally Harmonized System) classifications, chemical inventories from the European Chemicals Agency (ECHA), and specific hazard lists from the U.S. Environmental Protection Agency (EPA). We prioritize datasets that offer peer-reviewed or regulatory-cleared information.
    
    __What is the Hazard Tier Summary?__
    
    The Hazard Tier Summary is a classification system used to simplify complex toxicological data into four distinct categories. This allows users to quickly assess the level of known or suspected harm associated with a specific chemical based on the strength and type of available evidence.  The Tier Graphic provides a summary of several hazard classes at a glance.

    * __Tier 1: High Certainty Hazards__ This tier includes chemicals with well-documented, severe hazards. These classifications are based on the official Globally Harmonized System (GHS) and represent recognized dangers such as carcinogenicity, mutagenicity, reproductive toxicity, or high acute toxicity.

    * __Tier 2: Potential or Emerging Hazards__ This tier provides an expanded perspective by including chemicals that may not yet have a formal GHS "Category 1" status but show significant evidence of concern. This includes data from peer-reviewed scientific literature, predictive models (such as QSAR), and regulatory watchlists from agencies that go beyond standard GHS conclusions.

    * __Tier 3: Low to Moderate Hazard__ Tier 3 is assigned to chemicals that have been robustly studied and demonstrated to have a low or moderate hazard profile. These substances generally do not meet the criteria for the more severe classifications found in Tiers 1 and 2.

    * __Tier 4: Data Deficient__ This tier indicates that there is insufficient information to make a confident hazard assessment. It is important to note that a Tier 4 designation does not imply that a chemical is "safe"; rather, it highlights a lack of public testing or reporting, suggesting a precautionary approach is necessary.
    
    __How does the Aggregator address the lack of information?__
    
    For many chemicals on the list, the lack of available information is a critical issue. While it is often difficult to assess the true safety of a substance when data is sparse, the Aggregator is specifically designed to address this "information gap" in the following ways:

    * Multi-Source Synthesis: Rather than relying on a single regulatory body, the Aggregator looks across dozens of sources—including the EPA, ECHA, and international GHS databases—to compile many existing fragments of evidence. If a chemical is missing from one database, the tool seeks it out in others to paint a more complete picture.

    * The "Data Deficient" Designation (Tier 4): One of the most important functions of the Aggregator is to explicitly label chemicals where information is missing. By categorizing these as Tier 4, the tool ensures that "no data" is never mistaken for "no hazard." This transparency allows researchers to identify which substances require urgent testing.

    * Harmonizing Discrepancies: Sometimes one agency may classify a chemical while another does not. The Aggregator highlights these discrepancies, showing users exactly what is known by some and ignored by others.

    * Visualizing the Unknown: By centralizing what is available and what is not, the Aggregator provides a "landscape" of chemical knowledge. This helps users understand the weight of evidence (or the lack thereof) behind the materials they are researching, making it easier to apply the precautionary principle where data is thin.
    
    
    
    
    
"""
    return s

# --- Helper functions for markdown generation ---

def _add_GHS_icon(hcode):
    # take the first match
    for cl in config.HAZARD_MAP.keys():
        for lv in ['1','2']:
            if hcode in config.HAZARD_MAP[cl][lv]:
                if lv == '1':
                    return f" {':red_square:'} ({cl}) "
                return f" {':orange_square:'} ({cl}) "
    return ""

def _add_ECHA_indus_icon(hcode):
    # only return orange square
    for cl in config.HAZARD_MAP.keys():
        for lv in ['1','2']:
            if hcode in config.HAZARD_MAP[cl][lv]:
                return f" {':orange_square:'} ({cl}) "
    return ""

def _add_ci_icon(civar,icon=':orange_square:'):
    # only return orange square
    for cl in config.CHEMINFO_CATEGORY_MAP.keys():
       if civar in config.CHEMINFO_CATEGORY_MAP[cl]:
                return f" {icon} ({cl}) "
    return ""


def _has_showable_codes(hcodes):
    try:
        return ('H3' in hcodes) | ('H4' in hcodes)
    except:
        return False

def _get_echa_text(cas):
    try:
        cas_dir = os.path.join(config.RAW_CAS_DIR, cas)
        # print(cas_dir)
        for fn in os.listdir(cas_dir):
            if "ECHA_Info_hazard_su" in fn:
                with open(os.path.join(cas_dir, fn), 'r') as f:
                    s = f.read()
                s = s.replace('Additionally', '\n\n    **Additionally**')
                s = s.replace('Danger! ', '**DANGER!** ')
                s = s.replace('Warning', '**Warning**')
                # add note about change
                s += '<br><br>**(Update 3/2026)** In the recent reorganization of their website, ECHA has retired these "summaries".  See detailed data in ECHA CHEM data pages'
                return s
    except FileNotFoundError:
        return ""
    return ""

def _add_echa_summary(cas):
    # ECHA summary - OBSOLETE: ECHA stop posting it
    echa_text = _get_echa_text(cas)
    echatitle = 'ECHA summary'
    first_word = echa_text.split(' ')[0]
    
    admonition_type = 'info'
    if 'DANGER' in first_word:
        admonition_type = 'danger'
    elif 'Warning' in first_word:
        admonition_type = 'warning'
    elif 'NO' in first_word:
        admonition_type = 'note'
    return admonition_type, echatitle, echa_text
    

def _get_authoritative_indicators_text(t,ghs_dict):
    content = ''
    if len(t)>0:
        for j,jrow in t.iterrows():
            if jrow.source=='ECHA self-classified industry': continue
            if (not jrow.GHS_H_Codes):
                continue
            if (len(jrow.GHS_H_Codes)<2):
                continue
            content += f'    === "{jrow.source}"\n'
            # print(jrow.CASRN,jrow.source,jrow.GHS_H_Codes)
            codes = jrow.GHS_H_Codes.replace('Not found','')
            codelst = list(set(codes.replace(';',',').replace(' ','').split(',')))
            codelst.sort()
            for code in codelst:
                if len(code)<2:
                    continue
                if not code[1] in ['3','4']: # show only Health end Env hazards
                    continue
                try:
                    content += f'        * {_add_GHS_icon(code)}{code}: {ghs_dict[code]}\n'
                except:
                    content += f'        * <<{code}>> : unknown code\n'
    if content != '':
        return  '??? "Expand for details"\n\n' + content 
    return '<center> <b>No data</b> </center> \n\n'
    
def _get_gemini_text(cas):
    import json
    fn = os.path.join(config.PROCESSED_CAS_DIR,cas,'gemini_answers.json')
    if os.path.exists(fn):
        with open(fn,'r') as f:
            jstr = f.read()
        return json.loads(jstr)
    return {}
        
def _get_other_indicators_text(t,cas,ghs_dict,cidf):
    content = ''
    if len(t)>0:
        for j,jrow in t.iterrows():
            if jrow.source!='ECHA self-classified industry': continue
            if (not jrow.GHS_H_Codes):
                continue
            if (len(jrow.GHS_H_Codes)<2):
                continue
            content += f'    === "{jrow.source}"\n'
            # print(jrow.CASRN,jrow.source,jrow.GHS_H_Codes)
            codes = jrow.GHS_H_Codes.replace('Not found','')
            codelst = list(set(codes.replace(';',',').replace(' ','').split(',')))
            codelst.sort()
            for code in codelst:
                if len(code)<2:
                    continue
                if not code[1] in ['3','4']: # show only Health end Env hazards
                    continue
                # try:
                content += f'        * {_add_ECHA_indus_icon(code)}{code}: {ghs_dict[code]}\n'
                # except:
                #     content += f'    * <<{code}>> : unknown code\n'

    # now add the ChemInformatics V and H codes
    citmp = cidf[cidf.CASRN==cas].copy().drop(['CASRN','Name','DTXSID'],axis=1).reset_index(drop=True)
    citmp = citmp.fillna('ND')
    if len(citmp)==1:
        filtered_df = citmp.loc[:, citmp.iloc[0].isin(['H', 'VH', 'M'])]
        out = filtered_df.T.reset_index()
        out.columns = ['civar','cilevel']
        if len(out)>0:
            out.cilevel = out.cilevel.str.replace('VH','**very high**')
            out.cilevel = out.cilevel.str.replace('H','**high**')
            out.cilevel = out.cilevel.str.replace('M','moderate')
            if len(out)>0:
                content += '    === "ChemInformatics"\n'
                out = out.sort_values('cilevel')
                for j,jrow in out.iterrows():
                    content += f'        * {_add_ci_icon(jrow.civar,icon=":orange_square:")}{jrow.civar}: {jrow.cilevel}\n'
    if content != '':
        return  '??? "Expand for details"\n\n' + content 
    return '<center> <b>No data</b> </center> \n\n'

def _get_tier_3_text(t,cas,cidf):
    content= ''
    citmp = cidf[cidf.CASRN==cas].copy().drop(['CASRN','Name','DTXSID'],axis=1).reset_index(drop=True)
    citmp = citmp.fillna('ND')
    if len(citmp)==1:
        filtered_df = citmp.loc[:, citmp.iloc[0].isin(['L'])]
        out = filtered_df.T.reset_index()
        out.columns = ['civar','cilevel']
        if len(out)>0:
            out.cilevel = out.cilevel.str.replace('L','low')
            if len(out)>0:
                content += '    === "ChemInformatics"\n'
                out = out.sort_values('cilevel')
                for j,jrow in out.iterrows():
                    content += f'        * {jrow.civar}{_add_ci_icon(jrow.civar,icon=':blue_square:')}: {jrow.cilevel}\n'
    if content != '':
        return  '??? "Expand for details"\n\n' + content 
    return '<center> <b>No data</b> </center> \n\n'
            
    
# --- Main Generator Functions ---

def create_summary_table(df):
    """Generates an interactive HTML table of all chemicals."""
    
    # Prepare dataframe for the table
    table_df = df.copy()
    table_df['CASRN'] = table_df['casrn'].apply(lambda x: f'<a href="../../chemicals/{x}.html" target="_top">{x}</a>')
 
    # Use a 2-level relative path for the table in docs/assets/tables/
    table_df['tier_analysis'] = table_df['casrn'].apply(
            lambda x: f'<img src="../../images/{x}.svg" alt="Tier summary" width="150">'
    )

    table_df = table_df.rename(
        columns={'epa_pref_name': 'chem_name', 'alttxt': 'tier search'}
    )
    
    # Generate HTML
    html = itables.to_html_datatable(
        table_df[:outsize][['CASRN', 'chem_name', 'tier_analysis', 'concerns', 'low_hazard', 'groups', 'tier search','orig_source',]],
        **config.ITABLES_SETTINGS
    )
    
    # Custom CSS for consistent styling
    custom_css = """
    <style>
      body, table {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        font-size: 0.9rem;
        color: #333;
      }
    </style>
    """

    # Write to file
    with open(config.HTML_TABLE_OUT, 'w', encoding='utf-8') as f:
        f.write(html + custom_css)
    print(f"HTML summary table saved to {config.HTML_TABLE_OUT}")

separator = '\n--- \n'

def create_chemical_pages(chem_df, ghs_df):
    """Generates a markdown page for each chemical."""
    
    ghs_df = pd.read_parquet(config.GHS_DATA_PQ)
    # ci_df = pd.read_parquet(config.CHEMINFO_DATA_PQ)
    ci_df = pd.read_parquet(config.CHEMINFO_HAZARD_OUTPUT_PATH)
    ghs_dict = dp.get_ghs_codes()

    
    lists_of_lists = lols.List_of_list()

    # Ensure the output directory exists
    os.makedirs(config.CHEMICAL_MD_OUT_DIR, exist_ok=True)
    
    num_pages = len(chem_df)
    for i, row in chem_df[:outsize].iterrows():
        cas = row.casrn
        print('.',end='')
        gemini_dict = _get_gemini_text(cas)

        # hide left pane
        content = """---
hide:
  - navigation
---
"""
        content += getProlog()

        content += '#### Looking for a different chemical?  [To Chemical Index](../index.md){ .md-button .md-button--primary } {: style="text-align: right" } \n\n'
        content += separator

        # Start building markdown content
        content += f'# {row.casrn}: {row.chem_name}\n\n'
        
        # Show Header
        llcc = lists_of_lists.get_markdown_list_by_type(cas,"concern")
        llb = lists_of_lists.get_markdown_list_by_type(cas,"benign")
        llg = lists_of_lists.get_markdown_list_by_type(cas,"group")
        # echa_sum = _add_echa_summary(cas)
        echa_sum = ""  # now obsolete
        content += cph.get_chem_page_header(cas, 
                                            ing_name=row.chem_name,
                                            g_dict = gemini_dict,
                                            lists_of_concern=llcc,
                                            lists_of_benign=llb,
                                            lists_of_groups=llg,
                                            echasum = echa_sum,
                                            infosrv=infosrv)
        

        ## end Summary Header  ##
        
        # ECHA summary   
        # admonition_type, echatitle, echa_text = _add_echa_summary(cas)         
        # content += f'??? {admonition_type} "{echatitle}"\n\n    {echa_text}\n\n'

        # Tier summary image
        content += '## SOURCES\n\n'
        content += '### Chemical-specific data for tier generation\n'
        # content += f'![tier graphic summary]({config.TIER_IMAGE_URL.format(cas_num=cas)})\n\n'
        
        # Tier 1 & 2 Details
        # (Logic from your notebook is complex and preserved here)
        # ... [Your detailed logic for parsing GHS and ChemInformatics data would go here] ...
        # This part remains complex and could be further refactored into smaller functions.
        # For brevity, I'm showing the structure.
        t = ghs_df[ghs_df.CASRN==cas].copy()
        t['has_showable_codes'] = t.GHS_H_Codes.map(lambda x: _has_showable_codes(x))
        t = t[(t.GHS_H_Codes.str[0].isin(['H','E'])) & t.has_showable_codes]

        # Example for Authoritative
        content += '#### Authoritative indicators of hazards (GHS)\n\n'
        content += _get_authoritative_indicators_text(t, ghs_dict)
        
        # Example for Still hazardous
        content += '#### Other indications of hazards\n\n'
        content += _get_other_indicators_text(t, cas, ghs_dict, ci_df)


        # Example for Tier 3
        content += '#### Affirmative data showing low concern\n\n'
        content += _get_tier_3_text(t, cas, ci_df)

        content += '## GENERAL REFERENCES\n\n'
        content += '\n\n--8<-- "includes/source_desc_1.md"\n'
        content += '\n\n--8<-- "includes/ghs_hazard_tiers_extended.md"\n'
        
        
        # Write the file
        out_path = os.path.join(config.CHEMICAL_MD_OUT_DIR, f'{cas}.md')
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        if (i+1) % 50 == 0:
            print(f"Generated {i+1}/{num_pages} chemical pages...")

    print("All chemical pages generated.")
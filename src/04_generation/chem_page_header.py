# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 07:12:04 2025

@author: Gary
"""
import common

def get_chem_page_header(cas,ing_name,lists_of_concern):
    
    chem_img = common.getMoleculeImg(cas,size=150)
    haz_img = common.getHazChemImg(cas,size=400)
    scifi, repodic = common.getChemStructureInfo(cas)
    # print(chem_st)
    
    s = '<div class="grid cards" markdown> \n\n'
    
    s+= f'-   **{ing_name}**\n\n'
    s+= f'    CASRN: {cas}'
    # s+= '    ---\n\n'
    s+= f'    {chem_img}\n\n'
    
    s+= f'-   **Tier Profile**\n\n'
    # s+= f'    CASRN: {cas}'
    # s+= '    ---\n\n'
    s+= f'    {haz_img}\n\n'
    # s+= f'    Lists of concern: {lists_of_concern}\n\n'
    
    s+= f'-   **Lists of concern**\n\n'
    # s+= f'    CASRN: {cas}'
    # s+= '    ---\n\n'
    # s+= f'    {haz_img}\n\n'
    s+= f'    {lists_of_concern}\n\n'

    s+= f'-   **SciFinder data**\n\n'
    try:
        components = scifi["comp1"]+scifi["comp2"]
        s+= f'    Substance type: {scifi["subs_class"]}\n\n'
        s+= '    ---\n\n'
        if len(components)>0:
            s+= f'    Components: {components}\n\n'
        else:
            s+= '    (no components listed)\n\n'
        if len(scifi["subnotes"])>0:
            s+= f'    {scifi["subnotes"]}\n\n'
    except:
        s+= '     (No SciFinder data compiled)\n\n'
    
        
    s+= f'-   **EH Classification**\n\n'
    try:
        s+= f'    {repodic["eh_Class_L1"]}\n\n'
        s+= f'    ({repodic["eh_Class_L2"]})\n\n'
    except:
        s+='     (no repo data found for this chem)\n\n'        

    s+= f'-   **Group Membership**\n\n'
    s+=  '    (no repo data found for this chem)\n\n' 
    
    s+= '-   **Toxicological Profiles**\n\n'
    new_tab = '{: target="_blank" rel="noopener" }'
    
    lnk,name = common.getATSDR_info(cas)
    if len(lnk)>0:
        s+= f'    :white_check_mark: [ATSDR]({lnk}){new_tab} ({name}) \n\n'
    else:
        s+=  '    :x: ATSDR\n\n'

    lnk,name = common.getIRIS_info(cas)
    if len(lnk)>0:
        s+= f'    :white_check_mark: [IRIS]({lnk}){new_tab} ({name}) \n\n'
    else:
        s+=  '    :x: IRIS\n\n'


    name = common.get_Cmpd_of_Concern_info(cas)
    if len(name)>0:
        s+= f'    :white_check_mark: [Compound_of_Concern](https://environmentalhealthproject.shinyapps.io/compounds/){new_tab} ({name}) \n\n'
    else:
        s+=  '    :x: Compound_of_Concern\n\n'
           

    s+='</div>'

    
    return s
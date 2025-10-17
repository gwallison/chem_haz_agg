# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 07:12:04 2025

@author: Gary
"""
import common
import os
import re
import xml.etree.ElementTree as ET

imgdir = r"C:/MyDocs/integrated/chem_profiles/mkdocs/docs/assets/images"

def getTierImg_with_tooltips(cas, tooltip_data):
    """
    Reads an SVG file, parses it as XML to robustly inject data-tooltip attributes,
    and returns the full HTML block for inline display.
    """
    imgfn = os.path.join(imgdir, f'{cas}.svg')
    if not os.path.exists(imgfn):
        return f"<p>Error: SVG file not found for {cas}</p>"

    try:
        # Register the SVG namespace to find elements correctly.
        # This is a necessary step for parsing namespaced XML like SVG.
        ET.register_namespace('', "http://www.w3.org/2000/svg")
        # Explicitly register the 'xlink' namespace to prevent it from being renamed
        ET.register_namespace('xlink', "http://www.w3.org/1999/xlink")
        
        # Parse the entire SVG file into an XML tree structure
        tree = ET.parse(imgfn)
        root = tree.getroot()

        # Loop through the tooltip data
        for element_id, text in tooltip_data.items():
            # Use a proper XPath query to find the element with the matching id.
            # This is extremely reliable compared to string replacement.
            # The './/' searches the entire tree for the element.
            element_to_modify = root.find(f".//*[@id='{element_id}']")
            
            if element_to_modify is not None:
                # Sanitize text and set the 'data-tooltip' attribute
                safe_text = text.replace('"', '&quot;')
                element_to_modify.set('data-tooltip', safe_text)
            else:
                print(f"Warning: Could not find element with id='{element_id}' in {cas}.svg")

        # Convert the modified XML tree back into a string
        # 'unicode' encoding gives us a clean string without extra XML declarations.
        svg_content = ET.tostring(root, encoding='unicode')

    except ET.ParseError as e:
        return f"<p>Error parsing SVG file for {cas}: {e}</p>"

    # Embed the complete, modified SVG string into the final HTML
    outtxt = f"""<div class="svg-container">{svg_content}</div>
<div id="tooltip"></div>"""
    
    return outtxt

def get_chem_page_header(cas,ing_name,lists_of_concern):
    
    chem_img = common.getMoleculeImg(cas,size=150)
    haz_img = common.getHazChemImg(cas,size=400)
    scifi, repodic = common.getChemStructureInfo(cas)
    # print(chem_st)
    
    s = '<div class="grid cards 1" markdown> \n\n'
    
    s+= f'-   **{ing_name}**\n\n'
    s+= f'    {chem_img}\n\n'
    s+= f'    <center>CASRN: **{cas}**</center>\n\n'
    # get EH classification
    try:
        s+= f'    Classification:<br>'
        s+= f'    {repodic["eh_Class_L1"]}<br>'
        s+= f'    ({repodic["eh_Class_L2"]})\n\n'
    except:
        pass
    # s+= '    ---\n\n'
    
    s+= f'-   **Group Membership**\n\n'
    s+=  '    (no repo data found for this chem)\n\n' 
    
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
    
        
    # s+= f'-   **EH Classification**\n\n'
    # try:
    #     s+= f'    {repodic["eh_Class_L1"]}\n\n'
    #     s+= f'    ({repodic["eh_Class_L2"]})\n\n'
    # except:
    #     s+='     (no repo data found for this chem)\n\n'        

    
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
           

    s += '</div>\n\n'  # <-- CLOSE the grid cards div here.

    tooltip_data_for_this_chem = {
        'overall_tier_box': f"The overall rating for {ing_name} is based on its most severe hazard classification.",
        'cmr_box': "CMR Hazard: Text explaining the Carcinogenic, Mutagenic, or Reproductive toxicity goes here.",
        'edc_box': "EDC Hazard: Text explaining the Endocrine Disrupting Chemical concerns goes here.",
        'env_box': "ENV Hazard: Text about Environmental hazards goes here.",
        'ihl_box': "IHL Hazard: Text about Inhalation hazards goes here.",
        'orl_box': "ORL Hazard: Text about Oral hazards goes here.",
        'skn_box': "SKN Hazard: Text about Dermal and Eye hazards goes here.",
        
    }
    tiertxt = getTierImg_with_tooltips(cas, tooltip_data_for_this_chem)
    s += '## Tier Profile\n\n'
    s += f'{tiertxt}\n\n'    



    
    return s
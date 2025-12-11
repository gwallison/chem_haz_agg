# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 07:12:04 2025

@author: Gary
"""
import common
import os
import re
import xml.etree.ElementTree as ET
import config

test = """
??? note "Grid Example"
    This admonition contains a grid with two separate blocks of content.

    <div class="grid" markdown>

    <div markdown>
    ### Left Column
    * Item 1
    * Item 2
    * Item 3
    </div>

    <div markdown>
    ### Right Column
    > This is a blockquote in the right column.
    > Grids allow arranging elements like this.
    </div>

    </div>    
"""

# imgdir = r"C:/MyDocs/integrated/chem_profiles/mkdocs/docs/images"
# imgdir = config.TIER_IMAGE_DIR
# --- MODIFICATION: Build a robust path ---

# Get the absolute path of the current script file
# (ex: .../project_root/src/04_generation/chem_page_header.py)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Go up two levels to get to the project root
# (from 04_generation -> src -> project_root)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))

# Now, build the correct, absolute path to the images directory
imgdir = os.path.join(PROJECT_ROOT, 'mkdocs', 'docs', 'images')
# --- END MODIFICATION ---

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

        # Make the SVG scalable so it fills its container
        if 'width' in root.attrib:
            del root.attrib['width']  # Remove fixed width
        if 'height' in root.attrib:
            del root.attrib['height'] # Remove fixed height
        
        root.set('width', '100%') # Set width to 100% of its container

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

#     # Embed the complete, modified SVG string into the final HTML
#     outtxt = f"""<div class="svg-container">{svg_content}</div>
# <div id="tooltip"></div>"""

    # Set the width to 400px. This will double the height from ~75px to 150px.
    outtxt = f"""<div class="svg-container" style="width: 400px;">{svg_content}</div>
<div id="tooltip"></div>"""    

    return outtxt

def _chem_def_text(name,cas,class1,class2,img):
    opttext = f"""
    * :file_folder: [Chem Class](https://open-ff.org/fracfocus-chemical-classification-index/) level 1: __{class1}__
    * :file_folder: Chem Class level 2: __{class2}__
"""

    if class1=='':
        opttext = ''

    text = f"""
??? info "Chemical details of {name}"
    ### Chemical Identity
    * :octicons-beaker-16:  {name}
    * :id: CASRN: {cas}
{opttext}

    ### Chemical Structure
    {img}
"""
    return text
def get_chem_page_header(cas,ing_name,g_dict,
                         lists_of_concern,lists_of_groups,
                         infosrv):
    import evidence_generator as eg
    
    separator = '\n--- \n'
    
    chem_img = common.getMoleculeImg(cas,size=200)
    # haz_img = common.getHazChemImg(cas,size=400)
    scifi, repodic = common.getChemStructureInfo(cas)
    
    s = ''    
    # 1. Get the evidence data AND the final tier data
    evidence_data, final_tiers = eg.get_evidence_for_casrn(cas)
    
    # 2. Define mappings for SVG IDs and full names
    svg_id_map = {
        'CMR': 'cmr_box',
        'EDC': 'edc_box',
        'ENV': 'env_box',
        'IHL': 'ihl_box',
        'ORL': 'orl_box',
        'SKN': 'skn_box',
        'OGN': 'ogn_box'
        # Add 'OGN': 'ogn_box' if you have it
    }
    
    hazard_full_names = {
        'CMR': 'Carcinogenic, Mutagenic, or Reproductive Toxicity',
        'EDC': 'Endocrine Disruption',
        'ENV': 'Environmental Hazard',
        'IHL': 'Inhalation Hazard',
        'ORL': 'Oral Hazard',
        'SKN': 'Dermal/Eye Hazard',
        'OGN': 'Organ Hazard' 
    }



    # 3. Build the final tooltip dictionary
    trunc_ing = '???'
    if ing_name != None:
        trunc_ing = ing_name
    trunc_ing = str(trunc_ing)
    if len(trunc_ing)>20:
        trunc_ing = trunc_ing[:20]+'... '
    tooltip_data_for_svg = {
        'overall_tier_box': f"The <b>overall tier profile </b> for {ing_name} is based on its most severe hazard class."
    } 

    # Loop through all possible hazard categories
    for hazard_key, element_id in svg_id_map.items():
        
        # Get the full name and final tier
        full_name = hazard_full_names.get(hazard_key, f"{hazard_key} Hazard")
        final_tier = final_tiers.get(hazard_key, "Tier 4") # Default to Tier 4 if not found
        
        # Create the title string
        title_str = f"<b>{full_name}: {final_tier}</b>"

        # Check if we have evidence for this category
        if 'error' not in evidence_data and hazard_key in evidence_data:
            # We have evidence. Join it with <br>
            evidence_text = '<br>'.join(evidence_data[hazard_key])
            # Combine title and evidence
            tooltip_data_for_svg[element_id] = f"{title_str}<br>{evidence_text}"
        else:
            # No evidence found for this category (e.g., Tier 4)
            # Just show the title and a "no data" message
            tooltip_data_for_svg[element_id] = f"{title_str}<br>No indicators found for this tier."
            
    # --- Build the info about data completeness
    is_unspecified = 'unspec' in infosrv.get_scifinder_molecule(cas).lower()
    subs = infosrv.get_scifinder_substance_class(cas)
    has_generic = 'generic' in subs.lower()
    has_manual =  'manual'  in subs.lower()
    has_incomplete = 'incomplete' in subs.lower()
    has_concept = 'concept' in subs.lower()
    numref = infosrv.get_scifinder_numref(cas)

    # --- Start building the header string
    
    s+= '??? note "Looking for a different chemical?"\n'
    s+= '    If you are looking for a different chemical, please use the **Chemical Index** page to filter and search the complete catalog. (Using the "Search" bar above instead of the index may cause the profile|hover function to not work.)\n\n'

    s+= '    [**Go to Chemical Index**](../index.md)\n\n'
    # ---  Chem Definition Admonition
    try:
        class1 = repodic["eh_Class_L1"]
        class2 = repodic["eh_Class_L2"]
    except:
        class1 = ''
        class2 = ''
    chemdef = _chem_def_text(ing_name, cas, class1, class2, chem_img)
    # print(chemdef)
    s+= chemdef
    
    
    # s+= test
    # # s+= f'??? info "TEST Chemical details of {ing_name}"\n'
    # s+= '<div class="grid cards" markdown>\n\n'
    
    # s+= f'- :octicons-beaker-16:  __{ing_name}__\n'
    # s+= f'- :id: CASRN: __{cas}__ \n'
    # try:
    #     s+= f'- :file_folder: [Chem Class](https://open-ff.org/fracfocus-chemical-classification-index/) level 1:<br> __{repodic["eh_Class_L1"]}__ \n'
    #     s+= f'- :file_folder: Chem Class level 2:<br> __{repodic["eh_Class_L2"]}__ \n'
    # except:
    #     pass
    # s+= f'- {chem_img}\n'

    # s+= '</div>\n\n'

    # s+= f'??? info "Chemical details of {ing_name}"\n'
    # # s += '<div class="grid cards 1" markdown> \n\n'

    # s+= f'    -    **{ing_name}**\n\n'
    # s+= f'         {chem_img}\n\n'
    # s+= f'         <center>CASRN: **{cas}**</center>\n\n'
    # s+= f'         <center>Molecular formula: {infosrv.get_scifinder_molecule(cas)}</center>\n\n'
    # comp = infosrv.get_scifinder_components_as_list(cas)
    # if len(comp)>0:
    #     s+= f'    -    **Components of {cas}**:\n\n'
    #     s+= f'         {comp}\n\n'
    # # get EH classification
    # try:
    #     tmp = ''
    #     tmp += '    -    [**Chemical Classification**](https://open-ff.org/fracfocus-chemical-classification-index/) (Elsner and Holzer):<br>'
    #     tmp += f'        {repodic["eh_Class_L1"]}<br>'
    #     tmp += f'        ({repodic["eh_Class_L2"]})\n\n'
    #     s += tmp
    # except:
    #     s += '    Chemical classification not available\n\n'
    # # s += '</div>\n\n'  # <-- CLOSE the grid cards div here.

    # # s += f'    Measures of data deficiency:\n\n'
    # # s += f'    Molecular formula not specified: {is_unspecified}\n\n'
    # # s += f'    Substance class poorly defined: {has_generic|has_manual|has_incomplete|has_concept}\n\n'
    # # s += f'    Number of reference (via SciFinder): {numref}\n\n'
 
    tiertxt = getTierImg_with_tooltips(cas, tooltip_data_for_svg)
    s += '## "Hazard Profile" \n\n'
    if 'Q1' in g_dict.keys():
        answer = g_dict['Q1']
    else:
        answer = 'no summary generated yet'
    s += f'**Our Tier Summary**: {answer}\n\n'
    s += '*Tap or hover over each box for more detail.*\n\n'
    s += f'<center>{tiertxt}</center>\n\n'    

    s += separator
    s+= '## "Lists of Concern"? \n'
    if 'Q2' in g_dict.keys():
        answer = g_dict['Q2']
    else:
        answer = 'no summary generated yet'
    
    s+= f'{answer}\n'
    if len(lists_of_concern)>0:
        s+= '??? danger "List of Concerns **Details**"\n'
        s+= f'{lists_of_concern}\n\n'
    s += separator
    
    s+= f'## How complete is the understanding of this chemical? \n'
    if 'Q3' in g_dict.keys():
        answer = g_dict['Q3']
    else:
        answer = 'no summary generated yet'
    
    s+= f'{answer}\n'
    # if len(lists_of_concern)>0:
    #     s+= '??? danger "List of Concerns **Details**"\n'
    #     s+= f'{lists_of_concern}\n\n'
    s += separator
        
    # s += '<div class="grid cards 1" markdown> \n\n'
    
    # s+= f'-   **{ing_name}**\n\n'
    # s+= f'    {chem_img}\n\n'
    # s+= f'    <center>CASRN: **{cas}**</center>\n\n'
    # # get EH classification
    # try:
    #     s+= f'    Classification:<br>'
    #     s+= f'    {repodic["eh_Class_L1"]}<br>'
    #     s+= f'    ({repodic["eh_Class_L2"]})\n\n'
    # except:
    #     pass
    # # s+= '    ---\n\n'
    
    # s+= f'-   **Group Membership**\n\n'
    # s+= f'{lists_of_groups}\n\n'
    
    # s+= f'-   **Lists of concern**\n\n'
    # s+= f'{lists_of_concern}\n\n'

    # s+= f'-   **SciFinder data**\n\n'
    # try:
    #     components = scifi["comp1"]+scifi["comp2"]
    #     s+= f'    Substance type: {scifi["subs_class"]}\n\n'
    #     s+= '    ---\n\n'
    #     if len(components)>0:
    #         s+= f'    Components: {components}\n\n'
    #     else:
    #         s+= '    (no components listed)\n\n'
    #     if len(scifi["subnotes"])>0:
    #         s+= f'    {scifi["subnotes"]}\n\n'
    # except:
    #     s+= '     (No SciFinder data compiled)\n\n'
    

    
    # s+= '-   **Toxicological Profiles**\n\n'
    # new_tab = '{: target="_blank" rel="noopener" }'
    
    # lnk,name = common.getATSDR_info(cas)
    # if len(lnk)>0:
    #     s+= f'    :white_check_mark: [ATSDR]({lnk}){new_tab} ({name}) \n\n'
    # else:
    #     s+=  '    :x: ATSDR\n\n'

    # lnk,name = common.getIRIS_info(cas)
    # if len(lnk)>0:
    #     s+= f'    :white_check_mark: [IRIS]({lnk}){new_tab} ({name}) \n\n'
    # else:
    #     s+=  '    :x: IRIS\n\n'


    # name = common.get_Cmpd_of_Concern_info(cas)
    # if len(name)>0:
    #     s+= f'    :white_check_mark: [Compound_of_Concern](https://environmentalhealthproject.shinyapps.io/compounds/){new_tab} ({name}) \n\n'
    # else:
    #     s+=  '    :x: Compound_of_Concern\n\n'
           

    # s += '</div>\n\n'  # <-- CLOSE the grid cards div here.

    # --- MODIFICATION START ---
    

    return s
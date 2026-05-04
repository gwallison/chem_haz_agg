# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 07:12:04 2025

@author: Gary
"""
import common
import os
# import re
import xml.etree.ElementTree as ET
import config



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



def getTierImg(cas):
    """
    Reads an SVG file, makes it scalable, and returns the HTML block 
    for inline display without tooltip data.
    """
    imgfn = os.path.join(imgdir, f'{cas}.svg')
    if not os.path.exists(imgfn):
        return f"<p>Error: SVG file not found for {cas}</p>"

    try:
        # Register namespaces to ensure XML integrity
        ET.register_namespace('', "http://www.w3.org/2000/svg")
        ET.register_namespace('xlink', "http://www.w3.org/1999/xlink")
        
        tree = ET.parse(imgfn)
        root = tree.getroot()

        # Ensure scalability by removing fixed dimensions
        if 'width' in root.attrib:
            del root.attrib['width']
        if 'height' in root.attrib:
            del root.attrib['height']
        
        root.set('width', '100%')

        # Convert the XML tree back into a string
        svg_content = ET.tostring(root, encoding='unicode')

    except ET.ParseError as e:
        return f"<p>Error parsing SVG file for {cas}: {e}</p>"

    # Wrap in the same container used by the tooltip version for visual consistency
    return f'<div class="svg-container" style="width: 400px;">{svg_content}</div>'


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

def _chem_def_text(infosrv,name,cas,class1,class2,img,
                   subs_class,oecd_grps,complst):
    opttext = f"""
    * :file_folder: [E&H Chemical Class](https://open-ff.org/fracfocus-chemical-classification-index/) L1: __{class1}__ ; L2: __{class2}__  
"""
#    * :file_folder: [E&H Chemical Class](https://open-ff.org/fracfocus-chemical-classification-index/) level 2: __{class2}__


    if class1=='':
        opttext = ''
        
    oecdtext = ''
    for grp in oecd_grps:
        oecdtext += f'    * :file_folder: [OECD group](https://hpvchemicals.oecd.org/ui/ChemGroup.aspx): __{grp}__\n'
        
    comptxt = ''
    for comp in complst:
        compname = infosrv.get_epa_pref_name(comp)
        comptxt += f'    * :id: CASRN: {comp} ; :octicons-beaker-16:  {compname}\n'
    if len(comptxt)>0:
        comptxt = f'    ### Components of {cas}\n'+comptxt
        
    text = f"""
??? info "Chemical details of {name}"
    ### Chemical Identity
    * :octicons-beaker-16:  {name}
    * :id: CASRN: {cas}
    * :file_folder: [Substance Class(s) (from SciFinder)](https://open-ff.org/the-substance-classes-of-fracfocus-materials/): __{subs_class}__
{opttext}
{oecdtext}
    ### Chemical Structure
    {img}
{comptxt}

"""
    return text

# def _component_desc(caslst):
#     if caslst == []:
#         return ""

def _get_tier_icon(tier):
    idic = {'Tier 1': ' :red_square: ',
            'Tier 2': ' :orange_square: ',
            'Tier 3': ' :blue_square: ',
            'Tier 4': ' :white_medium_square: '}
    return idic[tier]
    
def _get_tier_evidence_detail(evid_dict):
    content = ''
    for item in evid_dict.keys():
        tier = evid_dict[item][1]
        tier_icon = _get_tier_icon(tier)
        # print(f'\n\nEv item: {item}: contents: {evid_dict[item]}')
        content += f'=== "{tier_icon} {item}"\n\n'
        content += f'    <b><h4>{tier_icon} {evid_dict[item][0]} - {tier}</b></h2>\n\n'
        for ev in evid_dict[item][2]:
            content += f'    * {ev}\n'            
    if content != '':
        # return  '??? "Evidence for Tier levels"\n\n' + content 
        return  '### Evidence for Tier levels\n(Select category below for more detail)\n\n' + content 
    return '<center> <b>No Evidence?</b> </center> \n\n'

def _construct_evidence_dict(evid_data,final_tiers,ing_name):
    # dictionary {haz_code: (title,tier,[ev1,ev2,etc])}
    hazard_full_names = {
        'CMR': 'Carcinogenic, Mutagenic, or Reproductive Toxicity',
        'EDC': 'Endocrine Disruption',
        'ENV': 'Environmental Hazard',
        'IHL': 'Inhalation Hazard',
        'ORL': 'Oral Hazard',
        'SKN': 'Dermal/Eye Hazard',
        'OGN': 'Organ Hazard' 
    }
    lst = []
    for item in final_tiers.keys():
        # tier 3 should be the "lowest" level
        lst.append(final_tiers[item])
    if len(lst)>0:
        ov_tier = min(lst)
        if (ov_tier=='Tier 3') & ('Tier 4' in lst):
            ov_tier = 'Tier 4'
    else:
        ov_tier = 'Tier 4'

    evid_dict = {'Overall': (f"The overall tier level for {ing_name} is based on its most severe hazard class(es):",
                             ov_tier,[])} 
 
    # Loop through all possible hazard categories
    for hazard_key, full_name in hazard_full_names.items():
        
        # Get the full name and final tier
        final_tier = final_tiers.get(hazard_key, "Tier 4") # Default to Tier 4 if not found
        try:  # for those classes with evidence
            evid_dict[hazard_key] = (full_name,
                                     final_tier,
                                     evid_data[hazard_key])
        except:
            evid_dict[hazard_key] = (full_name,
                                     final_tier,
                                     ['<b> no data found</b>'])
    #     # Check if we have evidence for this category
    #     if 'error' not in evid_data and hazard_key in evid_data:
    #         # We have evidence. Join it with <br>
    #         evidence_text = '\n        * '.join(evid_data[hazard_key])
    #         # Combine title and evidence
    #         evid_dict[hazard_key] = f"{title_str}<br>{evidence_text}"
    #     else:
    #         # No evidence found for this category (e.g., Tier 4)
    #         # Just show the title and a "no data" message
    #         evid_dict[hazard_key] = f"{title_str}<br>No indicators found for this tier."
    # # print(evid_dict)
    return evid_dict
    
def get_chem_page_header(cas,ing_name,g_dict,
                         lists_of_concern,lists_of_benign,
                         lists_of_groups,
                         echasum,
                         infosrv):
    import evidence_generator as eg
    
    separator = '\n--- \n'
    
    chem_img = common.getMoleculeImg(cas,size=200)
    # haz_img = common.getHazChemImg(cas,size=400)
    scifi, repodic = common.getChemStructureInfo(cas)
    
    s = ''    
    # 1. Get the evidence data AND the final tier data
    # evidence_data, final_tiers = eg.get_evidence_for_casrn(cas)
    evid_data, final_tiers = eg.get_evidence_for_casrn(cas)
    
    # # 2. Define mappings for SVG IDs and full names
    # svg_id_map = {
    #     'CMR': 'cmr_box',
    #     'EDC': 'edc_box',
    #     'ENV': 'env_box',
    #     'IHL': 'ihl_box',
    #     'ORL': 'orl_box',
    #     'SKN': 'skn_box',
    #     'OGN': 'ogn_box'
    #     # Add 'OGN': 'ogn_box' if you have it
    # }
    
    # hazard_full_names = {
    #     'CMR': 'Carcinogenic, Mutagenic, or Reproductive Toxicity',
    #     'EDC': 'Endocrine Disruption',
    #     'ENV': 'Environmental Hazard',
    #     'IHL': 'Inhalation Hazard',
    #     'ORL': 'Oral Hazard',
    #     'SKN': 'Dermal/Eye Hazard',
    #     'OGN': 'Organ Hazard' 
    # }



    # # 3. Build the final tooltip dictionary
    # trunc_ing = '???'
    # if ing_name != None:
    #     trunc_ing = ing_name
    # trunc_ing = str(trunc_ing)
    # if len(trunc_ing)>20:
    #     trunc_ing = trunc_ing[:20]+'... '
    # tooltip_data_for_svg = {
    #     'overall_tier_box': f"The <b>overall tier profile </b> for {ing_name} is based on its most severe hazard class."
    # } 

    # # Loop through all possible hazard categories
    # for hazard_key, element_id in svg_id_map.items():
        
    #     # Get the full name and final tier
    #     full_name = hazard_full_names.get(hazard_key, f"{hazard_key} Hazard")
    #     final_tier = final_tiers.get(hazard_key, "Tier 4") # Default to Tier 4 if not found
        
    #     # Create the title string
    #     title_str = f"<b>{full_name}: {final_tier}</b>"

    #     # Check if we have evidence for this category
    #     if 'error' not in evidence_data and hazard_key in evidence_data:
    #         # We have evidence. Join it with <br>
    #         evidence_text = '<br>'.join(evidence_data[hazard_key])
    #         # Combine title and evidence
    #         tooltip_data_for_svg[element_id] = f"{title_str}<br>{evidence_text}"
    #     else:
    #         # No evidence found for this category (e.g., Tier 4)
    #         # Just show the title and a "no data" message
    #         tooltip_data_for_svg[element_id] = f"{title_str}<br>No indicators found for this tier."
            
    # --- Build the info about data completeness
    # is_unspecified = 'unspec' in infosrv.get_scifinder_molecule(cas).lower()
    subs = infosrv.get_scifinder_substance_class(cas)
    oecd_grp = infosrv.get_oecd_group(cas)
    # has_generic = 'generic' in subs.lower()
    # has_manual =  'manual'  in subs.lower()
    # has_incomplete = 'incomplete' in subs.lower()
    # has_concept = 'concept' in subs.lower()
    # numref = infosrv.get_scifinder_numref(cas)

    # --- Start building the header string

    # s+= '#### Looking for a different chemical?  [To Chemical Index](../index.md){ .md-button .md-button--primary } {: style="text-align: right" } \n\n'
    # s += separator
    
    # s += getProlog()
 
    # s+= '## BASICS\n\n'
    # ---  Chem Definition Admonition
    try:
        class1 = repodic["eh_Class_L1"].strip()
        class2 = repodic["eh_Class_L2"].strip()
    except:
        class1 = ''
        class2 = ''
    # subs
    complst = infosrv.get_scifinder_components_as_list(cas)
    chemdef = _chem_def_text(infosrv,ing_name, cas, 
                             class1, class2, chem_img,
                             subs, oecd_grp, complst)
    # print(chemdef)
    s+= chemdef
    
    
 
    # tiertxt = getTierImg_with_tooltips(cas, tooltip_data_for_svg)
    tiertxt = getTierImg(cas)


    s+= '## HAZARD EVIDENCE\n\n'

    s += """### Hazard Tiers
<div class="annotate" markdown>Tier levels(1) Hazard classes(2) </div>

1.    __Open-FF's Compiled Hazard Summary:__\n
      **Tier 1**: :red_square: Authoritative GHS record of substantial hazard\n
      **Tier 2**: :orange_square: Expanded perspective\n
      **Tier 3**: :blue_square: Demonstrated Low Hazard\n
      **Tier 4**: :white_medium_square: Data Deficient \n
2.    __Hazard classes:__ \n
      **CMR**: Carcinogen, Mutagen or Reproductive hazard\n
      **IHL**: Inhalation hazards\n
      **ORL**: Oral hazards\n
      **SKN**: Dermal and eye hazards\n
      **OGN**: Organ and systemic hazards\n
      **EDC**: Endocrine disruption hazards (note that GHS does not yet have comprehensive classification of EDCs. Therefore, the strongest hazard level in this system is effectively level 2)\n
      **ENV**: Environmental hazards\n
      
"""
    if 'Q1' in g_dict.keys():
        answer = g_dict['Q1']
    else:
        answer = 'no summary generated yet'

    s += f'**Our Tier Summary**: {answer}\n\n'
    # s += '<center> <i>Tap or hover over each box for evidence of Tier designation.</i> </center>\n\n'
    s += f'<center>{tiertxt}</center>\n\n'    

    ## tier evidence collapsible
    evid_dict = _construct_evidence_dict(evid_data, final_tiers,ing_name)
    s+= _get_tier_evidence_detail(evid_dict)

    s += separator
    s+= '### Lists of Concern and/or Low Hazard\n'
    if 'Q2' in g_dict.keys():
        answer = g_dict['Q2']
    else:
        answer = 'no summary generated yet'
    
    s+= f'{answer}\n'
    if len(lists_of_concern)>0:
        s+= '??? danger "List of Concerns: Details"\n'
        s+= f'{lists_of_concern}\n\n'
        
    # # ECHA summary - NOW OBSOLETE
    # if len(echasum[2])>0: # the text is non zero
    #     admonition_type, echatitle, echa_text = echasum         
    #     s += f'??? {admonition_type} "{echatitle}"\n\n    {echa_text}\n\n'
        
    
    if len(lists_of_benign)>0:
        s+= '??? info "Evidence of Low Hazard: Details"\n'
        s+= f'{lists_of_benign}\n\n'
    s += separator
    
    s+= '### How complete is the understanding of this chemical? \n'

    if 'Q3' in g_dict.keys():
        answer = g_dict['Q3']
    else:
        answer = 'no summary generated yet'
    
    s+= f'{answer}\n'

    s += separator

 
    s+= '### Links to Profiles and Data Sheets\n'
    s+= """These links, when active, connect you directly to original resources about this chemical.  If the resource is crossed out, that resource does not assess this chemical\n\n"""

    new_tab = '{: target="_blank" rel="noopener" }'
        
    lnk,name = common.getATSDR_info(cas)
    if len(lnk)>0:
        s+= f':material-check: [ATSDR]({lnk}){new_tab} (as {name}) \n\n'
    else:
        s+=  ':octicons-x-16: ~~ATSDR~~ \n\n'

    lnk,name = common.getCompTox_ref(cas)
    if len(lnk)>0:
        s+= f':material-check: [EPA CompTox]({lnk}){new_tab} (as {name}) \n\n'
    else:
        s+=  ':octicons-x-16: ~~EPA CompTox~~ \n\n'

    lnk,name = common.get_ECHA_data_page(cas)
    if len(lnk)>0:
        s+= f':material-check: [ECHA Chem substance]({lnk}){new_tab} (as {name}) \n\n'
    else:
        s+=  ':octicons-x-16: ~~ECHA Chem substance~~ \n\n'

    lnk,name = common.getNJ_RTK_info(cas)
    if len(lnk)>0:
        s+= f':material-check: [NJ Right-to-Know datasheet]({lnk}){new_tab} (as {name}) \n\n'
    else:
        s+=  ':octicons-x-16: ~~NJ Right-to-Know datasheet~~ \n\n'

    lnk,name = common.getIRIS_info(cas)
    if len(lnk)>0:
        s+= f':material-check: [IRIS]({lnk}){new_tab} (as {name}) \n\n'
    else:
        s+=  ':octicons-x-16: ~~IRIS~~ \n\n'

    lnk,name = common.getPPRTV_info(cas)
    if len(lnk)>0:
        s+= f':material-check: [PPRTV]({lnk}){new_tab} (as {name}) \n\n'
    else:
        s+=  ':octicons-x-16: ~~PPRTV~~ \n\n'

    name = common.get_Cmpd_of_Concern_info(cas)
    if len(name)>0:
        s+= f':material-check: [EHP Compounds of Concern](https://environmentalhealthproject.shinyapps.io/compounds/){new_tab} (as {name}) \n\n'
    else:
        s+=  ':octicons-x-16: ~~EHP Compounds of Concern~~ \n\n'

    lnk,name = common.get_niosh_pocket_info(cas)
    if len(lnk)>0:
        s+= f':material-check: [NIOSH Pocket Guide]({lnk}){new_tab} (as {name}) \n\n'
    else:
        s+=  ':octicons-x-16: ~~NIOSH Pocket Guide~~ \n\n'

    res = common.get_cameo_info(cas)
    if len(res)>0:
        for row in res:
            s+= f':material-check: [CAMEO]({row[0]}){new_tab} (as {row[1]}) \n\n'
    else:
        s+=  ':octicons-x-16: ~~CAMEO~~ \n\n'
        
    lnk,name = common.get_oecd_chemical_page(cas)
    if len(lnk)>0:
        s+= f':material-check: [OECD reference page]({lnk}){new_tab} (as {name}) \n\n'
    else:
        s+=  ':octicons-x-16: ~~OECD reference page~~ \n\n'
               
 
    

    return s
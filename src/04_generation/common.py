# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 07:20:27 2025

@author: Gary
"""
import os
import pandas as pd

pic_base_url = "https://storage.googleapis.com/open-ff-browser/images/"
local_pic_dir = r"C:\MyDocs\integrated\openFF\images\pic_dir"

def getMoleculeImg(cas,size=120,#use_remote=False,link_up_level=0,
                   alt=None,
                   unavail_text="<center>Image not available</center>"):
    # returns an html image link
    
    if alt:
        alttext = alt
    else:
        alttext = f'Molecular structure of {cas}'
    #see if the image file is local, and therefore available in the browser
    ct_path = os.path.join(local_pic_dir,cas,'comptoxid.png')
    # take comptox version if it exists
    print(ct_path)
    if os.path.exists(ct_path):
        # and is not empty:  # this is the normal return
        if os.path.getsize(ct_path) > 0:
            return f"""<center><img src="{pic_base_url}{cas}/comptoxid.png" alt="{alttext}" onerror="this.onerror=null; this.remove();" width="{size}"></center>"""
    else: # but if all else fails, try linking to chemid
        # print('ct_path didt exist')
        ci_path = os.path.join(local_pic_dir,cas,'chemid.png')
        if os.path.exists(ci_path):
            if os.path.getsize(ci_path) > 0:
                return f"""<center><img src="{pic_base_url}/{cas}/chemid.png" alt="{alttext}" onerror="this.onerror=null; this.remove();" width="{size}"></center>"""
    return unavail_text

def getFingerprintImg(cas,size=140,alt=None):
    # returns an html image link when possible
    # check if we have it locally, but link to the cloud version
    fp_path = os.path.join(local_pic_dir,cas,'haz_fingerprint.png')
    # take comptox version if it exists
    cas_ignore = ['7732-18-5','proprietary','conflictingID',
                  'ambiguousID','sysAppMeta','cas_not_assigned']
    if alt:
        alttext = alt
    else:
        alttext = f'EPA Cheminformatics classifications of {cas}'

    if cas in cas_ignore:
        return ' <center>---</center> '
    if os.path.exists(fp_path):
        return f"""<center><img src="https://storage.googleapis.com/open-ff-browser/images/{cas}/haz_fingerprint.png" alt="{alttext}"  onerror="this.onerror=null; this.remove();" width={size}></center>"""
    return "<center>ChemInformatics not available</center>"
    
def getHazChemImg(cas,size=140,alt=None):
    # returns an html image link when possible
    # check if we have it locally, but link to the cloud version
    fp_path = os.path.join(r"C:\MyDocs\integrated\chem_profiles_old\code\tmp\tier_fig",
                           f'{cas}.png')
    # take comptox version if it exists
    cas_ignore = ['7732-18-5','proprietary','conflictingID',
                  'ambiguousID','sysAppMeta','cas_not_assigned']
    if alt:
        alttext = alt
    else:
        alttext = f'Open-FF compiled tier summary of {cas}'

    if cas in cas_ignore:
        return ' <center>---</center> '
    print(fp_path)
    if os.path.exists(fp_path):
        return f"""<center><img src="https://storage.googleapis.com/open-ff-browser/images/ChemHazTier/{cas}.png" alt="{alttext}"  onerror="this.onerror=null; this.remove();" width={size}></center>"""
    return "<center>Tier analysis not available</center>"
    
def getChemStructureInfo(cas):
    fn = r"G:\My Drive\webshare\scrape_data\SciFinder_chem_pages\scifinder_df.parquet"
    try:
        scifi_df = pd.read_parquet(fn)
        t = scifi_df.set_index('bgCAS')
        dic = t.loc[cas].to_dict()
    except:
        dic = {}
    fn = r"C:\MyDocs\integrated\repos\openFF_data_2025_04_20\pickles\bgCAS.parquet"
    try:
        repoCAS = pd.read_parquet(fn)
        t = repoCAS.set_index('bgCAS')
        repodic = t.loc[cas].to_dict()
    except:
        repodic = {}
    return dic, repodic

def getATSDR_info(cas):
    # ATSDR
    fn = r"C:/MyDocs/integrated/chem_profiles/data/02_intermediate/atsdr_casrn.parquet"
    t = pd.read_parquet(fn)
    t = t[t.CASRN==cas]
    try:
        return t.ATSDR_link.tolist()[0], t.Chemical_Name.tolist()[0]
    except:
        return '',''

def getIRIS_info(cas):
    # IRIS
    fn = r"C:/MyDocs/integrated/chem_profiles/data/02_intermediate/iris_data.parquet"
    t = pd.read_parquet(fn)
    t = t[t.CASRN==cas]
    try:
        return t.URL.tolist()[0], t.chemical_name.tolist()[0]
    except:
        return '',''

def get_Cmpd_of_Concern_info(cas):

    fn = r"C:/MyDocs/integrated/chem_profiles/data/02_intermediate/Compounds_of_Concern.parquet"
    t = pd.read_parquet(fn)
    t = t[t.CASRN==cas]
    try:
        return  t['name'].tolist()[0]
    except:
        return ''
    
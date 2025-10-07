# -*- coding: utf-8 -*-
"""
Created on Mon Oct  6 16:19:53 2025

@author: Gary

Currently there is no offical list of the chemicals at CoC, so
we must construct it by hand.
"""
import os
import pandas as pd

in_lst = [
    ('79-34-5', '1,1,2,2-Tetrachloroethane'),
    ('106-93-4','1,2-Dibromoethane'),
    ('107-06-2','1,2-Dichloroethane'),
    ('78-87-5','1,2-Dichloropropane'),
    ('75-07-0','Acetaldehyde'),
    ('67-64-1','Acetone'),
    ('75-05-8','Acetonitrile'),
    ('107-02-8','Acrolein'),
    ('107-13-1','Acrylonitrile'),
    ('7440-38-2','Arsenic, inorganic compounds'),
    ('71-43-2','Benzene'),
    ('50-32-8','Benzo(a)pyrene'),
    ('7440-41-7','Beryllium'),
    ('126-99-8','beta-Chloroprene'),
    ('106-99-0','Butadiene (1,3-Butadiene)'),
    ('7440-43-9','Cadmium'),
    ('75-15-0','Carbon disulfide'),
    ('56-23-5','Carbon tetrachloride'),
    ('7782-50-5','Chlorine'),
    ('75-01-4','Chloroethylene; Vinyl chloride'),
    ('67-66-3','Chloroform (Trichloromethane)'),
    ('16065-83-1','Chromium (III) compounds'),
    ('18540-29-9','Chromium (VI) compounds'),
    ('75-09-2','Dichloromethane'),
    ('64-17-5','Ethanol'),
    ('141-78-6','Ethyl acetate'),
    ('100-41-4','Ethylbenzene'),
    ('75-21-8','Ethylene oxide'),
    ('50-00-0','Formaldehyde'),
    ('302-01-2','Hydrazine'),
    ('7783-06-4','Hydrogen Sulfide'),
    ('7439-92-1','Lead'),
    ('108-31-6','Maleic Anhydride'),
    ('7439-96-5','Manganese'),
    ('7439-97-6','Mercury'),
    ('74-87-3','Methyl chloride'),
    ('110-54-3','n-Hexane'),
    ('91-20-3','Naphthalene'),
    ('7440-02-0','Nickel'),
    ('10102-44-0','Nitrogen Dioxide'),
    ('10028-15-6','Ozone'),
    ('106-46-7','p-Dichlorobenzene'),
    ('100-42-5','Styrene'),
    ('127-18-4','Tetrachloroethylene'),
    ('108-88-3','Toluene'),
    ('584-84-9','Toluene-2,4-diisocyanate (TDI)'),
    ('79-01-6','Trichloroethylene'),
    ('121-44-8','Triethylamine'),
    ('1330-20-7','Xylenes')  ]

def generate_df():
    df = pd.DataFrame(in_lst,columns=['CASRN','name'])
    outdir = r'C:/MyDocs/integrated/chem_profiles/data/02_intermediate'
    df.to_parquet(os.path.join(outdir,'Compounds_of_Concern.parquet'))
    
if __name__ == '__main__':
    generate_df()
    
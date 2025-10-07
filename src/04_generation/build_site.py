# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 11:00:46 2025

@author: Gary
"""

# build.py

import data_processing as dp
import page_generators as pg

def main():
    """Main function to build the mkdocs site content."""
    
    print("--- Starting site generation ---")
    
    # 1. Load and process all chemical data
    chem_summary_df = dp.load_and_prepare_data()
    
    # 2. Get GHS codes
    ghs_codes_df = dp.get_ghs_codes()
    
    # 3. Generate the main interactive HTML table
    pg.create_summary_table(chem_summary_df)
    
    # 4. Generate individual markdown pages for each chemical
    pg.create_chemical_pages(chem_summary_df, ghs_codes_df)
    
    print("\n--- Site generation complete! ---")
    print("You can now run 'mkdocs serve' in your terminal.")

if __name__ == '__main__':
    main()
# build.py

import sys
import os
import argparse
import shutil

# Add the project root to the Python path to resolve the 'config' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config
import data_processing as dp
import page_generators as pg

def main():
    """Main function to build the mkdocs site content."""
    parser = argparse.ArgumentParser(description="Build the mkdocs site content.")
    parser.add_argument("--dev", action="store_true", help="Run in dev mode (build only 10 chemical pages for fast preview)")
    args = parser.parse_args()
    
    if args.dev:
        print("--- Starting site generation (DEV mode: 10 pages) ---")
        pg.outsize = 10
    else:
        print("--- Starting site generation (FULL mode) ---")
        pg.outsize = None
        
    # Clear the output chemicals directory to prevent live-reload overload
    if os.path.exists(config.CHEMICAL_MD_OUT_DIR):
        print(f"Cleaning output directory: {config.CHEMICAL_MD_OUT_DIR}")
        # Shutil.rmtree handles deleting directories recursively
        shutil.rmtree(config.CHEMICAL_MD_OUT_DIR)
    os.makedirs(config.CHEMICAL_MD_OUT_DIR, exist_ok=True)
    
    # 1. Load and process all chemical data
    chem_summary_df = dp.load_and_prepare_data()
    
    # 2. Get GHS codes
    ghs_codes_df = dp.get_ghs_codes()
    
    # 3. Generate the main interactive HTML table
    pg.create_summary_table(chem_summary_df)
    
    # 4. Generate individual markdown pages for each chemical
    pg.create_chemical_pages(chem_summary_df, ghs_codes_df)
    
    print("\n--- Site generation complete! ---")
    if args.dev:
        print("Dev preview build finished. Live reload will be near-instantaneous.")
    print("You can run 'mkdocs serve' in your terminal.")

if __name__ == '__main__':
    main()
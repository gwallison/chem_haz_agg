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
import make_graphics

def main():
    """Main function to build the mkdocs site content."""
    parser = argparse.ArgumentParser(description="Build the mkdocs site content.")
    parser.add_argument("--dev", action="store_true", help="Run in dev mode (build only 10 chemical pages for fast preview)")
    parser.add_argument("--casrns", help="Comma-separated CASRNs to regenerate, leaving all other existing pages untouched")
    args = parser.parse_args()

    target_casrns = [c.strip() for c in args.casrns.split(",")] if args.casrns else None

    if args.dev:
        print("--- Starting site generation (DEV mode: 10 pages) ---")
        pg.outsize = 10
    elif target_casrns:
        print(f"--- Starting site generation (SCOPED mode: {len(target_casrns)} CASRNs) ---")
        pg.outsize = None
    else:
        print("--- Starting site generation (FULL mode) ---")
        pg.outsize = None

    if target_casrns is None:
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

    # 3. Regenerate tier graphics (skipped in --dev: full mode only, keeps fast preview fast)
    if not args.dev:
        print("Regenerating tier SVGs...")
        make_graphics.generate_all_tier_graphics(casrns=target_casrns)

    # 4. Generate the main interactive HTML table (always covers every chemical,
    #    even in scoped mode, so the searchable index stays complete)
    pg.create_summary_table(chem_summary_df)

    # 5. Generate individual markdown pages for each chemical (scoped to
    #    target_casrns when given, leaving all other pages as-is)
    pages_df = chem_summary_df[chem_summary_df.casrn.isin(target_casrns)] if target_casrns else chem_summary_df
    pg.create_chemical_pages(pages_df, ghs_codes_df)
    
    print("\n--- Site generation complete! ---")
    if args.dev:
        print("Dev preview build finished. Live reload will be near-instantaneous.")
    print("You can run 'mkdocs serve' in your terminal.")

if __name__ == '__main__':
    main()
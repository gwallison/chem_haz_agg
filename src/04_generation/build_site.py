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


def sync_molecule_images(casrns):
    """
    Copies molecule structure images from the per-CAS asset hub
    (config.PROCESSED_CAS_DIR) into the mkdocs docs tree so they ship as
    static assets with the built site. `casrns` is the list of CAS to sync,
    or None to sync every CAS that has a local image.
    """
    if casrns is None:
        casrns = [
            d for d in os.listdir(config.PROCESSED_CAS_DIR)
            if os.path.isdir(os.path.join(config.PROCESSED_CAS_DIR, d))
        ]

    copied = 0
    for cas in casrns:
        src = os.path.join(config.PROCESSED_CAS_DIR, cas, config.MOLECULE_IMAGE_FILENAME)
        if not os.path.exists(src) or os.path.getsize(src) == 0:
            continue
        dst_dir = os.path.join(config.MOLECULE_IMAGES_SITE_DIR, cas)
        dst = os.path.join(dst_dir, config.MOLECULE_IMAGE_FILENAME)
        os.makedirs(dst_dir, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1
    print(f"Synced {copied} molecule image(s) to the site.")


def main():
    """Main function to build the mkdocs site content."""
    parser = argparse.ArgumentParser(description="Build the mkdocs site content.")
    parser.add_argument("--dev", action="store_true", help="Run in dev mode (build only 10 chemical pages for fast preview)")
    parser.add_argument("--casrns", help="Comma-separated CASRNs to regenerate, leaving all other existing pages untouched")
    parser.add_argument("--new-only", action="store_true", help="Regenerate only chemicals that don't yet have a tier SVG (new since the last full build)")
    args = parser.parse_args()

    if args.new_only:
        target_casrns = make_graphics.find_casrns_missing_tier_svg()
        print(f"--new-only: {len(target_casrns)} chemical(s) have no existing tier SVG.")
        if not target_casrns:
            print("Nothing new to generate.")
            return
    else:
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
        print("Syncing molecule images...")
        sync_molecule_images(casrns=target_casrns)

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
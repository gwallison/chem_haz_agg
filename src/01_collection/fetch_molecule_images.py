# -*- coding: utf-8 -*-
"""
Fetches molecule structure images (PNG) from EPA CompTox, keyed by DTXSID,
and stores them in the per-CAS asset hub (config.PROCESSED_CAS_DIR). This is
the canonical, local-to-ChemHaz replacement for the old sibling-project
pic_dir + GCS bucket setup.

Usage:
    python src/01_collection/fetch_molecule_images.py
    python src/01_collection/fetch_molecule_images.py --casrns 100-01-6,100-02-7
"""
import sys
import os
import argparse
import time
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config
import epa_api_client as eac

SLEEP_BETWEEN_FETCHES = 2  # seconds, be polite to the EPA API


def image_path(cas):
    return os.path.join(config.PROCESSED_CAS_DIR, cas, config.MOLECULE_IMAGE_FILENAME)


def ensure_molecule_images(casrns=None):
    """
    Fetches missing molecule images for the given CASRNs (or the whole
    master list if casrns is None). Skips CAS already covered locally, and
    CAS EPA has already told us have no structure image (hasStructureImage
    == False in epa_chem_master.parquet), so no network call is wasted.
    """
    epadf = pd.read_parquet(config.EPA_CHEM_MASTER)
    if casrns is not None:
        epadf = epadf[epadf.casrn.isin(casrns)]

    fetched, skipped_known_absent, skipped_existing, failed = 0, 0, 0, 0

    for _, row in epadf.iterrows():
        cas = row.casrn
        dtxsid = row.dtxsid
        path = image_path(cas)

        if os.path.exists(path):
            skipped_existing += 1
            continue

        if row.get('hasStructureImage') is False or row.get('hasStructureImage') == 0:
            skipped_known_absent += 1
            continue

        if not isinstance(dtxsid, str) or not dtxsid.startswith('DTX'):
            continue

        print(f'Fetching molecule image for {cas} ({dtxsid})...')
        content = eac.get_chemical_image(dtxsid)
        if content is None:
            print(f'  ...request failed for {cas}, leaving for next run')
            failed += 1
            continue

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(content)  # empty bytes preserved as "checked, none available"

        if content:
            print(f'  ...got it ({len(content)} bytes)')
            fetched += 1
        else:
            print('  ...EPA returned no image')

        time.sleep(SLEEP_BETWEEN_FETCHES)

    print(f'\nDone. fetched={fetched}, already_present={skipped_existing}, '
          f'known_absent={skipped_known_absent}, failed={failed}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Fetch molecule structure images from EPA CompTox.")
    parser.add_argument("--casrns", help="Comma-separated CASRNs to fetch, instead of the full master list")
    args = parser.parse_args()

    target_casrns = [c.strip() for c in args.casrns.split(",")] if args.casrns else None
    ensure_molecule_images(casrns=target_casrns)

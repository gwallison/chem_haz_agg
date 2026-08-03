# -*- coding: utf-8 -*-
"""
Consolidates the per-CASRN ECHA search-result CSVs (produced by
ECHA_substance_scraper_1.py, saved in config.ECHA_PAGES) into the single
CASRN -> substance_ID/link lookup table at config.ECHA_SUBSTANCE_LINKS.

Reuses the row-filtering logic from ECHA_substance_scraper_2.py so a CSV
row is only kept here if it would also have been accepted there.
"""

import os
import sys
import pandas as pd

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config
from ECHA_substance_scraper_2 import load_chem_links_from_local_csv, filter_appropriate_rows


def build_substance_links():
    mastercas = pd.read_parquet(config.MASTER_CAS_LIST)
    casrn_list = mastercas.CASRN.tolist()

    records = []
    missing = 0
    for cas in casrn_list:
        csv_path = os.path.join(config.ECHA_PAGES, f'{cas}_search_res.csv')
        if not os.path.exists(csv_path):
            missing += 1
            continue

        df = load_chem_links_from_local_csv(csv_path)
        if df is None or df.empty:
            continue

        appropriate_rows, _ = filter_appropriate_rows(df, cas)
        for row in appropriate_rows:
            link = row.get('Substance Information Page')
            if not isinstance(link, str) or not link.startswith('http'):
                continue
            records.append({
                'CASRN': cas,
                'Name': row.get('Name'),
                'ec_number': row.get('EC / List Number'),
                'substance_link': link,
                'substance_ID': link.rstrip('/').split('/')[-1],
            })

    print(f"{len(casrn_list)} master CASRNs checked: {missing} had no search_res.csv, "
          f"{len(records)} substance links found.")

    out_df = pd.DataFrame(records)
    out_df.to_parquet(config.ECHA_SUBSTANCE_LINKS, index=False)
    print(f"Saved {len(out_df)} rows to {config.ECHA_SUBSTANCE_LINKS}")
    return out_df


if __name__ == '__main__':
    build_substance_links()

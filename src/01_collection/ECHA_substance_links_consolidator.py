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


def is_timeout_placeholder_csv(csv_path):
    """
    True if this search_res.csv looks like the empty-DataFrame fallback that
    ECHA_substance_scraper_1.py writes when the CSV download button couldn't be
    found within its timeout (a network/UI hiccup during the scrape, not
    necessarily a real "no results" from ECHA). Real ECHA exports always have
    a title row, a blank/meta row, and a header row before any data.
    """
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            line_count = sum(1 for _ in f)
        return line_count < 3
    except OSError:
        return False


def build_substance_links():
    mastercas = pd.read_parquet(config.MASTER_CAS_LIST)
    casrn_list = mastercas.CASRN.tolist()

    records = []
    missing = 0
    timed_out = 0
    parse_errors = 0
    retry_candidates = []
    for cas in casrn_list:
        csv_path = os.path.join(config.ECHA_PAGES, f'{cas}_search_res.csv')
        if not os.path.exists(csv_path):
            missing += 1
            continue

        if is_timeout_placeholder_csv(csv_path):
            timed_out += 1
            retry_candidates.append(cas)
            continue

        df = load_chem_links_from_local_csv(csv_path)
        if df is None:
            parse_errors += 1
            continue
        if df.empty:
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
          f"{timed_out} had a timed-out/empty search placeholder (candidates for re-scrape), "
          f"{parse_errors} failed to parse for other reasons, "
          f"{len(records)} substance links found.")

    if retry_candidates:
        with open(config.ECHA_SEARCH_TIMEOUT_RETRIES, 'w', encoding='utf-8') as f:
            f.write('\n'.join(retry_candidates) + '\n')
        print(f"Wrote {len(retry_candidates)} CASRNs to retry to {config.ECHA_SEARCH_TIMEOUT_RETRIES} "
              f"-- re-run ECHA_substance_scraper_1.py --retry-timeouts to re-attempt them.")

    out_df = pd.DataFrame(records)
    out_df.to_parquet(config.ECHA_SUBSTANCE_LINKS, index=False)
    print(f"Saved {len(out_df)} rows to {config.ECHA_SUBSTANCE_LINKS}")
    return out_df


if __name__ == '__main__':
    build_substance_links()

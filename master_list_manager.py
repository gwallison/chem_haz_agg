import pandas as pd
from pathlib import Path
import datetime
import os
import re
import shutil
import argparse
import numpy as np
import config

# Define the path to the master file.

MASTER_FILE_FN = config.MASTER_CAS_LIST
MASTER_COLUMNS = ['CASRN', 'orig_source', 'date_added','DTXSID','ec_numbers']

# Standard CAS Registry Number shape: 2-7 digits, dash, 2 digits, dash, 1 check digit.
CASRN_FORMAT_RE = re.compile(r'^\d{2,7}-\d{2}-\d$')

def get_master_df():
    return pd.read_parquet(MASTER_FILE_FN)

def _backup_master_file() -> str | None:
    """Copies the current master file to a timestamped backup before it's overwritten."""
    if not os.path.exists(MASTER_FILE_FN):
        return None
    backup_dir = config.MASTER_CAS_LIST_BACKUP_DIR
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup_path = os.path.join(backup_dir, f'master_cas_list_{ts}.parquet')
    shutil.copy2(MASTER_FILE_FN, backup_path)
    return backup_path

def save_master_df(df):
    """Backs up the current master file, then writes the updated version."""
    _backup_master_file()
    df.to_parquet(MASTER_FILE_FN, index=False, engine='pyarrow')
    df.to_csv(config.TEMP_CASRN_CSV)

def save_temp_csv():
    """  used to make a copy of the master that is easy to copy and paste from"""
    df = get_master_df()
    df.to_csv(config.TEMP_CASRN_CSV)


def _normalize_casrn(raw) -> str | None:
    """Strips whitespace and leading zeros (first segment); returns None if unusable."""
    if not isinstance(raw, str):
        return None
    cas = raw.strip()
    if not cas:
        return None
    parts = cas.split('-')
    if len(parts) == 3:
        parts[0] = parts[0].lstrip('0') or '0'
        cas = '-'.join(parts)
    return cas


def _passes_cas_checksum(cas: str) -> bool:
    """Validates the CAS Registry Number check-digit algorithm."""
    body = cas.replace('-', '')
    check = int(body[-1])
    digits = [int(d) for d in body[:-1]]
    total = sum(d * (i + 1) for i, d in enumerate(reversed(digits)))
    return total % 10 == check


def quarantine_casrns(bad_rows: list[dict]) -> None:
    """Appends rejected CASRN rows to the running quarantine log (never overwritten)."""
    if not bad_rows:
        return
    qdf = pd.DataFrame(bad_rows)
    file_exists = os.path.exists(config.QUARANTINE_CASRN_CSV)
    qdf.to_csv(config.QUARANTINE_CASRN_CSV, mode='a', header=not file_exists, index=False)


def add_casrns(new_casrns: list[str], source: str) -> int:
    """
    Validates and adds new CASRNs to the master Parquet file.

    Pipeline: drop blank/unusable values -> drop known non-chemical
    placeholders (config.CAS_TO_IGNORE) -> normalize whitespace/leading
    zeros -> validate format + CAS check-digit (failures go to the
    quarantine log) -> dedupe against existing master entries -> append.
    """
    master_df = get_master_df()
    existing_casrns = {_normalize_casrn(c) for c in master_df['CASRN']}

    blank = 0
    ignored = 0
    quarantined_rows = []
    duplicates = 0
    to_add = []
    seen_this_batch = set()
    run_date = datetime.date.today()

    for raw in new_casrns:
        cas = _normalize_casrn(raw)
        if cas is None:
            blank += 1
            continue
        if cas in config.CAS_TO_IGNORE:
            ignored += 1
            continue
        if not CASRN_FORMAT_RE.match(cas):
            quarantined_rows.append({'CASRN': raw, 'orig_source': source,
                                      'reason': 'bad format', 'run_date': run_date})
            continue
        if not _passes_cas_checksum(cas):
            quarantined_rows.append({'CASRN': raw, 'orig_source': source,
                                      'reason': 'bad checksum', 'run_date': run_date})
            continue
        if cas in existing_casrns or cas in seen_this_batch:
            duplicates += 1
            continue
        seen_this_batch.add(cas)
        to_add.append(cas)

    quarantine_casrns(quarantined_rows)

    print(f"\n--- add_casrns: source '{source}' ---")
    print(f"  Rows submitted:               {len(new_casrns)}")
    print(f"  Blank/unusable:               {blank}")
    print(f"  Ignored (known non-chemical): {ignored}")
    print(f"  Quarantined (invalid):        {len(quarantined_rows)}")
    print(f"  Already in master (dupes):    {duplicates}")
    print(f"  New records added:            {len(to_add)}")

    if not to_add:
        print("No new records to add.")
        return 0

    new_records_df = pd.DataFrame({
        'CASRN': to_add,
        'orig_source': source,
        'date_added': pd.to_datetime(run_date)

    })

    if master_df.empty:
        updated_df = new_records_df
    else:
        updated_df = pd.concat([master_df, new_records_df], ignore_index=True)

    save_master_df(updated_df)
    print(f"Successfully added {len(to_add)} new records from source '{source}'.")
    return len(to_add)


def _log_removed_casrns(removed_rows: list[dict]) -> None:
    """Appends removed rows (full original record + reason) to the running removal log."""
    if not removed_rows:
        return
    rdf = pd.DataFrame(removed_rows)
    file_exists = os.path.exists(config.REMOVED_CASRN_LOG)
    rdf.to_csv(config.REMOVED_CASRN_LOG, mode='a', header=not file_exists, index=False)


def remove_casrns(casrns_to_remove: list[str], reason: str) -> int:
    """
    Removes CASRNs from the master list (e.g. to undo a mistaken add).

    Requires a reason so every removal is auditable. Backs up the master
    file before writing (via save_master_df) and appends the full
    original record for each removed row -- plus the reason and removal
    date -- to the running removal log, so a removal can be manually
    reconstructed later if it turns out to be wrong.
    """
    if not reason or not reason.strip():
        raise ValueError("A non-empty reason is required to remove CASRNs.")

    master_df = get_master_df()
    targets = {_normalize_casrn(c) for c in casrns_to_remove}
    targets.discard(None)

    normalized_master = master_df['CASRN'].apply(_normalize_casrn)
    mask = normalized_master.isin(targets)
    removed_df = master_df[mask]

    if removed_df.empty:
        print("No matching CASRNs found in master list. Nothing removed.")
        return 0

    not_found = targets - set(normalized_master[mask])
    remaining_df = master_df[~mask].reset_index(drop=True)

    run_date = datetime.date.today()
    log_rows = []
    for _, row in removed_df.iterrows():
        rec = row.to_dict()
        rec['reason'] = reason
        rec['removed_date'] = run_date
        log_rows.append(rec)
    _log_removed_casrns(log_rows)

    save_master_df(remaining_df)

    print(f"Removed {len(removed_df)} record(s) from master list. Reason: {reason}")
    if not_found:
        print(f"Not found in master (no action taken): {sorted(not_found)}")
    return len(removed_df)


def casrn_exists(casrn: str) -> bool:
    """Checks if a single CASRN exists in the master list."""
    ## possible refactor: don't fetch whole file, use parquet filter for CASRN
    master_df = pd.read_parquet(MASTER_FILE_FN)
    return casrn in master_df['CASRN'].values

def casrns_exist(casrns_to_check: list[str]) -> dict:
    """Checks a list of CASRNs against the master list and sorts them."""
    master_df = pd.read_parquet(MASTER_FILE_FN)
    existing_casrns_set = set(master_df['CASRN'])
    found = [cas for cas in casrns_to_check if cas in existing_casrns_set]
    missing = [cas for cas in casrns_to_check if cas not in existing_casrns_set]
    return {'existing': found, 'missing': missing}

def _read_casrns_from_path(file_path: str | Path, column: str = 'CASRN') -> list:
    """Reads unique values from `column` in a .csv, .parquet, or .txt (one-per-line) file."""
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()
    if suffix == '.txt':
        return [line.strip() for line in file_path.read_text().splitlines() if line.strip()]
    if suffix == '.parquet':
        df = pd.read_parquet(file_path)
    elif suffix == '.csv':
        df = pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file extension '{suffix}' (use .csv, .parquet, or .txt).")
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in {file_path}. Available columns: {list(df.columns)}")
    return df[column].unique().tolist()


def add_casrns_from_file(file_path: str | Path, source_name: str, casrn_column: str = 'CASRN') -> int:
    """
    Extracts unique CASRNs from a CSV or parquet file (auto-detected by
    extension) and adds them.

    Args:
        file_path (str or Path): The path to the data file (.csv or .parquet).
        source_name (str): The name to assign as the source for these CASRNs.
        casrn_column (str, optional): The name of the column containing the CASRNs.
                                      Defaults to 'CASRN'.

    Returns:
        int: The number of new, unique records added to the master list.
    """
    try:
        unique_casrns = _read_casrns_from_path(file_path, casrn_column)
    except FileNotFoundError:
        print(f"Error: The file was not found at {file_path}")
        return 0
    except ValueError as e:
        print(f"Error: {e}")
        return 0

    print(f"Found {len(unique_casrns)} unique CASRNs in column '{casrn_column}' from source '{source_name}'.")

    num_added = add_casrns(new_casrns=unique_casrns, source=source_name)
    return num_added

# --- REFACTORED FracFocus FUNCTION ---
def add_from_FracFocus(file_path: str | Path = config.FF_WORKING_DATA) -> int:
    """
    Extracts CASRNs from a FracFocus file by calling the generic function.

    This is now a simple wrapper around the more flexible 'add_casrns_from_file'.
    """
    return add_casrns_from_file(
        file_path=file_path,
        source_name='FracFocus',
        casrn_column='bgCAS'  # Specify the non-default column name
    )

def print_summary():
    df = get_master_df()
    print('\n'+'='*10, ' MASTER CHEM LIST  Summary ','='*10,'\n')
    print(f'   Number of chemicals: {len(df):5}')
    print(f'            Num DTXSID: {len(df[df.DTXSIDs.notna()]):5}')
    print(f'            Num ec_ids: {len(df[df.ec_numbers.notna()]):5}\n')
    df = df.sort_values('date_added',ascending=False)
    print(f'   Most recent addition: {(df.iloc[0].date_added).date()}')
    print(f'   Most recent source: {(df.iloc[0].orig_source)}')
    print('='*49)
    
def add_from_build_nb(file_path: str | Path = config.OPENFF_BUILD_NEW_CAS) -> int:
    """
    Extracts CASRNs newly surfaced by the Open-FF build process and adds
    them to the master chem list.
    """
    return add_casrns_from_file(file_path, 'FracFocus', 'CASNumber')

def update_DTXSID():
    """
    Run this after fetching COMPTOX CASRN:DTXSID file.
    
    uses output of CompTox bulk summary EXCEL file to add
    any new DTXSID numbers to existing.  Looks for most recent xlsx file
    with appropriate prefix to use as source.


    Returns
    -------
    Number of records updated

    """
    def update_row(master_row,DTXSID):
        # import math
        # print(master_row.CASRN, DTXSID)
        if (pd.isna(DTXSID)):
            return master_row.DTXSIDs, False # don't change anything

        if isinstance(master_row.DTXSIDs, np.ndarray):
            wlst = list(master_row.DTXSIDs)
        else:
            print(type(master_row.DTXSIDs))
            wlst = []
            
        if not DTXSID in wlst:
            wlst.append(DTXSID)
            return wlst, True
        return master_row.DTXSIDs, False # keeps the value
            
    dlst = os.listdir(config.RAW_DATA)
    targets = []
    # print(dlst)
    for fn in dlst:
        fnlst = fn.split('_')
        # print(fn[-3:])
        if (fn[-3:] == 'csv') & (fnlst[0]=='CCD-Batch-Search'):
            # print(fn)
            targets.append(fn)

    targets.sort(reverse=True)
    # print(f'targets: {targets}')
    if len(targets)==0:
        print('NO APPROPRIATE *CSV* COMPTOX FILE IN RAW!  NOT UPDATED!')
        return 0
    
    ctdf = pd.read_csv(os.path.join(config.RAW_DATA,targets[0]))
    c = ctdf.DTXSID.notna()
    print(f'Using "{targets[0]}" as DTXSID source')
    total = len(ctdf)
    num = len(ctdf[c])
    print(f'   - CASRN with DTXSID: {num:,};  without: {total-num:,}')
    
    updated = []
    newdtxsid = []
    df = get_master_df()
    for i,row in df.iterrows():
        cas = row.CASRN
        epadtx = ctdf[ctdf.INPUT==cas].DTXSID.tolist()
        if len(epadtx)>1:
            print("MORE THAN ONE DTXSID! Need to change logic to capture!")
        dtxsid = epadtx[0] if epadtx else np.nan
        res = update_row(row, dtxsid)
        newdtxsid.append(res[0])
        if res[1]: updated.append(cas)
        
    df.DTXSIDs = newdtxsid
    
    # print(df.head())
    print(f' Updated: {len(updated)}')
    save_master_df(df)
    
def main():
    parser = argparse.ArgumentParser(
        description="Manage the ChemHaz master CASRN list (data/03_processed/master_cas_list.parquet).",
        epilog="All arguments are flags -- none are positional. Example:\n"
               "  python master_list_manager.py add-file --path \"C:\\path\\to\\file.parquet\" "
               "--source \"my_source_label\" --column CASRN\n"
               "Run `python master_list_manager.py <command> -h` for a command's full argument list.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest='command', required=True)

    p_add = sub.add_parser(
        'add-file',
        help='Add CASRNs from a one-off CSV or parquet file.',
        description="Add CASRNs from a one-off CSV or parquet file. --path and --source "
                     "are both required flags (not positional).",
        epilog="Example:\n"
               "  python master_list_manager.py add-file --path \"C:\\path\\to\\file.parquet\" "
               "--source \"my_source_label\" --column CASRN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p_add.add_argument('--path', required=True, help='Path (as a flag, not positional) to the source file (.csv or .parquet).')
    p_add.add_argument('--source', required=True,
                        help="Required. Short label recorded in the 'orig_source' column for every row added "
                             "this run, e.g. 'gwa_local_all_prod' (used later to trace where a CASRN came from).")
    p_add.add_argument('--column', default='CASRN',
                        help="Name of the column in the source file containing the CASRNs (default: 'CASRN'). "
                             "Only needed if the file uses a different column name.")

    p_ff = sub.add_parser('add-fracfocus',
                           help='Add CASRNs from the current FracFocus working_df (bgCAS column).')
    p_ff.add_argument('--path', default=config.FF_WORKING_DATA,
                       help=f'Override the default path ({config.FF_WORKING_DATA}).')

    p_bn = sub.add_parser('add-build-nb',
                           help='Add CASRNs newly surfaced by the Open-FF build (new_cas_added.parquet).')
    p_bn.add_argument('--path', default=config.OPENFF_BUILD_NEW_CAS,
                       help=f'Override the default path ({config.OPENFF_BUILD_NEW_CAS}).')

    p_rm = sub.add_parser('remove', help='Remove CASRNs from the master list (a reason is required).')
    p_rm.add_argument('--casrns', help='Comma-separated CASRNs to remove.')
    p_rm.add_argument('--file', help='Path to a .txt (one per line), .csv, or .parquet file listing CASRNs to remove.')
    p_rm.add_argument('--column', default='CASRN', help="Column name if --file is .csv/.parquet (default: 'CASRN').")
    p_rm.add_argument('--reason', required=True, help='Why these are being removed (logged to the removal log).')

    sub.add_parser('summary', help='Print master list summary stats.')
    sub.add_parser('update-dtxsid',
                    help='Merge in DTXSIDs from the most recent CompTox batch-search CSV in data/01_raw.')

    args = parser.parse_args()

    if args.command == 'add-file':
        add_casrns_from_file(args.path, args.source, args.column)
        print_summary()
    elif args.command == 'add-fracfocus':
        add_from_FracFocus(args.path)
        print_summary()
    elif args.command == 'add-build-nb':
        add_from_build_nb(args.path)
        print_summary()
    elif args.command == 'remove':
        casrns = []
        if args.casrns:
            casrns.extend(c.strip() for c in args.casrns.split(',') if c.strip())
        if args.file:
            try:
                casrns.extend(_read_casrns_from_path(args.file, args.column))
            except (FileNotFoundError, ValueError) as e:
                parser.error(str(e))
        if not casrns:
            parser.error("Provide CASRNs to remove via --casrns and/or --file.")
        remove_casrns(casrns, reason=args.reason)
    elif args.command == 'summary':
        print_summary()
    elif args.command == 'update-dtxsid':
        update_DTXSID()


if __name__ == '__main__':
    main()
    
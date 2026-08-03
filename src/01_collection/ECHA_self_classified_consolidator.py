#!/usr/bin/env python3

"""
Processes ECHA self-classification data to summarize hazard codes.

Reads a Parquet file of ECHA self-classifications, cleans the data,
and then summarizes it based on chemical identifiers (CASRN, ec_number).

The summary includes:
- total_tabs: The total number of classification tabs for that chemical.
- tabs_used_in_summary: The number of tabs that fall within the top 90%
  of company notifications (sorted by tab_order).
- all_hcodes: A list of all H-codes from those top 90% tabs.
- unique_hcodes: A set (unique list) of H-codes from those top 90% tabs.
"""

import pandas as pd
import sys
import os
import time

# Add the project root to the Python path to resolve the 'config' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config

# --- Configuration ---
# File paths
INPUT_PATH = config.ECHA_SELF_CLASSIFIED_PATH
OUTPUT_PATH = config.ECHA_SELF_SUMMARY_PATH

# Column names
GROUP_BY_COLS = ['CASRN', 'ec_number']
AGG_COL = 'Hazard statement code'
TAB_ORDER_COL = 'tab_order'
TAB_PERC_COL = 'tab_percentage'

# Processing parameters
PERCENTAGE_THRESHOLD = 90.0
# ----------------------------------------

def build_indus_bridge(final_summary_df, output_path):
    """
    Derives the classifier-ready per-CASRN GHS_H_Codes file
    (config.ECHA_INDUS_OUTPUT_PATH) from the detailed per-(CASRN,
    ec_number) summary, matching the plain comma-separated GHS_H_Codes
    string schema every other GHS source (PubChem, Australia, Japan,
    ChemInformatics) uses.
    """
    def flatten_codes(codes_lists):
        all_codes = set()
        for lst in codes_lists:
            all_codes.update(lst)
        return ', '.join(sorted(all_codes)) if all_codes else 'N/A'

    indus_df = final_summary_df.groupby('CASRN', as_index=False).agg(
        GHS_H_Codes=('unique_hcodes', flatten_codes)
    )
    indus_df['GHS_Pictograms'] = 'N/A'
    indus_df['GHS_Signals'] = 'N/A'
    indus_df['GHS_P_Codes'] = 'N/A'
    indus_df['Download_Date'] = time.strftime("%Y-%m-%d")

    indus_df.to_parquet(output_path, index=False)
    print(f"Also wrote classifier-ready bridge file ({len(indus_df)} CASRN) to: {output_path}")


def main():
    """
    Main function to read, process, and write the data.
    """
    try:
        print(f"Starting ECHA data processing...")

        # --- 1. Read Data ---
        print(f"Reading input file: {INPUT_PATH}")
        df = pd.read_parquet(INPUT_PATH)
        print(f"Successfully read {len(df)} rows.")

        # --- 2. Clean Data ---
        # Define all columns we need *before* dropping
        REQUIRED_COLS = GROUP_BY_COLS + [AGG_COL, TAB_ORDER_COL, TAB_PERC_COL]
        
        # Check if all required columns exist
        missing_cols = [col for col in REQUIRED_COLS if col not in df.columns]
        if missing_cols:
            raise KeyError(f"Missing expected columns: {missing_cols}")

        # We ONLY drop rows where TAB_PERC_COL is missing, as we need it for cumsum.
        # We KEEP rows where AGG_COL (H-code) is missing, as they count towards percentage.
        df_cleaned = df.dropna(subset=[TAB_PERC_COL])
        dropped_count = len(df) - len(df_cleaned)
        if dropped_count > 0:
            print(f"Dropped {dropped_count} rows with missing '{TAB_PERC_COL}'.")
        
        # --- 2.1. Calculate Total Tabs ---
        print("Calculating total number of tabs per chemical...")
        if df_cleaned.empty:
             print("Warning: No data left after cleaning. Output will be empty.")
             tab_counts_total = pd.DataFrame(columns=GROUP_BY_COLS + ['total_tabs'])
        else:
            tab_counts_total = df_cleaned.groupby(GROUP_BY_COLS, as_index=False).agg(
                total_tabs=(TAB_ORDER_COL, 'nunique')
            )
        print(f"Found {len(tab_counts_total)} chemicals with at least one tab.")
        
        # --- 2.5. Filter for Top 90% ---
        print(f"Filtering for top {PERCENTAGE_THRESHOLD}% of companies per chemical...")
        
        df_top_90 = pd.DataFrame() # Initialize empty
        
        if not df_cleaned.empty:
            try:
                # Create a new numeric percentage column.
                # Use .copy() to avoid SettingWithCopyWarning
                df_filtered = df_cleaned.copy()
                df_filtered[TAB_PERC_COL] = df_filtered[TAB_PERC_COL].str.replace('%', '', regex=False).astype(float)
            
            except ValueError as e:
                print(f"\n--- Error ---", file=sys.stderr)
                print(f"Could not convert '{TAB_PERC_COL}' to numeric.", file=sys.stderr)
                print(f"Ensure it's a string with '%' (e.g., '80.0%'). Error: {e}", file=sys.stderr)
                sys.exit(1)
            except AttributeError:
                # Handle case where it might already be numeric
                print(f"Warning: '{TAB_PERC_COL}' does not seem to be a string. Using as is.", file=sys.stderr)
                df_filtered[TAB_PERC_COL] = df_filtered[TAB_PERC_COL].astype(float)

            # --- START: New logic for correct percentage calculation ---
            
            # 1. Create a deduplicated dataframe for just the tabs and their percentages
            tab_percentage_cols = GROUP_BY_COLS + [TAB_ORDER_COL, TAB_PERC_COL]
            df_unique_tabs = df_filtered[tab_percentage_cols].drop_duplicates(
                subset=GROUP_BY_COLS + [TAB_ORDER_COL]
            )
            
            # 2. Sort this deduplicated list by tab order
            df_unique_tabs_sorted = df_unique_tabs.sort_values(by=GROUP_BY_COLS + [TAB_ORDER_COL])

            # 3. Calculate cumulative percentage *on the deduplicated list*
            df_unique_tabs_sorted['cumulative_perc'] = df_unique_tabs_sorted.groupby(GROUP_BY_COLS)[TAB_PERC_COL].cumsum()
            
            # 4. Shift to get the *starting* percentage for each tab
            df_unique_tabs_sorted['cumulative_perc_shifted'] = df_unique_tabs_sorted.groupby(GROUP_BY_COLS)['cumulative_perc'].shift(1, fill_value=0)
            
            # 5. Get the list of "allowed" tabs that fall under the threshold
            allowed_tabs = df_unique_tabs_sorted[df_unique_tabs_sorted['cumulative_perc_shifted'] < PERCENTAGE_THRESHOLD]
            
            # 6. Use this list of allowed tabs to filter the original (non-deduplicated) dataframe
            # This correctly selects all H-codes belonging to the top 90% of tabs.
            df_top_90 = df_filtered.merge(
                allowed_tabs[GROUP_BY_COLS + [TAB_ORDER_COL]],  # The list of allowed (CASRN, ec_number, tab_order)
                on=GROUP_BY_COLS + [TAB_ORDER_COL],
                how='inner'
            )
            # --- END: New logic ---
            
            # Calculate dropped rows based on the original filtered data
            filter_rows_dropped = len(df_filtered) - len(df_top_90)
            print(f"Dropped {filter_rows_dropped} rows falling outside the top {PERCENTAGE_THRESHOLD}% threshold.")
        else:
             print("Skipping 90% filter as no data was available after cleaning.")

        # --- 3. Process Data ---
        print(f"Grouping by {GROUP_BY_COLS} and aggregating data (from top {PERCENTAGE_THRESHOLD}%)...")

        # 1. Aggregate tab counts (using the full top 90% set *before* dropping NaN H-codes)
        if df_top_90.empty:
            tabs_used_summary = pd.DataFrame(columns=GROUP_BY_COLS + ['tabs_used_in_summary'])
        else:
            tabs_used_summary = df_top_90.groupby(GROUP_BY_COLS, as_index=False).agg(
                tabs_used_in_summary=(TAB_ORDER_COL, 'nunique')
            )
        print(f"Aggregation complete. {len(tabs_used_summary)} chemicals had tabs in the top {PERCENTAGE_THRESHOLD}%.")

        # 2. Aggregate H-codes (dropping NaNs from AGG_COL first)
        df_top_90_with_hcodes = df_top_90.dropna(subset=[AGG_COL])
        
        if df_top_90_with_hcodes.empty:
             hcode_summary = pd.DataFrame(columns=GROUP_BY_COLS + ['all_hcodes', 'unique_hcodes'])
        else:
            hcode_summary = df_top_90_with_hcodes.groupby(GROUP_BY_COLS, as_index=False).agg(
                all_hcodes=(AGG_COL, list),
                unique_hcodes=(AGG_COL, 'unique')
            )
        print(f"Found {len(hcode_summary)} chemicals with at least one H-Code in the top {PERCENTAGE_THRESHOLD}%.")

        # 3. Merge H-code and tab count summaries
        collapsed_df = pd.merge(
            tabs_used_summary,
            hcode_summary,
            on=GROUP_BY_COLS,
            how='outer' # Use outer to keep both lists, then merge with total
        )

        # --- 3.5. Merge Total Counts with Summary ---
        print("Merging H-code summary with total tab counts...")
        final_summary_df = pd.merge(
            tab_counts_total,
            collapsed_df,
            on=GROUP_BY_COLS,
            how='outer' # Keep all chemicals from both lists.
        )

        # --- 4. Defensive Cleaning and Column Creation ---
        print("Cleaning final dataframe and ensuring all columns exist...")

        # Define a function to fill list-like columns
        def fill_list_na(col_series):
            """Fills NaNs in a pandas Series with empty lists."""
            # Check for object type, otherwise .apply will fail
            if col_series.dtype == 'object':
                return col_series.apply(lambda x: [] if (isinstance(x, float) and pd.isna(x)) or x is None else x)
            else:
                # If column is not object (e.g., all float NaNs), create empty lists
                return [[] for _ in range(len(col_series))]

        # Check and fill 'total_tabs' (in case of outer merge from empty tab_counts_total)
        if 'total_tabs' not in final_summary_df.columns:
            final_summary_df['total_tabs'] = 0
        else:
            final_summary_df['total_tabs'] = final_summary_df['total_tabs'].fillna(0).astype(int)

        # Check and fill 'tabs_used_in_summary'
        if 'tabs_used_in_summary' not in final_summary_df.columns:
            final_summary_df['tabs_used_in_summary'] = 0
        else:
            final_summary_df['tabs_used_in_summary'] = final_summary_df['tabs_used_in_summary'].fillna(0).astype(int)

        # Check and fill 'all_hcodes'
        if 'all_hcodes' not in final_summary_df.columns:
            final_summary_df['all_hcodes'] = [[] for _ in range(len(final_summary_df))]
        else:
            final_summary_df['all_hcodes'] = fill_list_na(final_summary_df['all_hcodes'])

        # Check and fill 'unique_hcodes'
        if 'unique_hcodes' not in final_summary_df.columns:
            final_summary_df['unique_hcodes'] = [[] for _ in range(len(final_summary_df))]
        else:
            final_summary_df['unique_hcodes'] = fill_list_na(final_summary_df['unique_hcodes'])

        # pandas 3.0's default Arrow-backed string dtype can't infer a type
        # for cells holding numpy arrays (from the 'unique' aggregation) mixed
        # with plain Python lists; normalize both list columns to plain lists.
        final_summary_df['all_hcodes'] = final_summary_df['all_hcodes'].apply(list)
        final_summary_df['unique_hcodes'] = final_summary_df['unique_hcodes'].apply(list)

        # --- 5. Write Output ---
        print(f"Writing summary to: {OUTPUT_PATH}")
        
        print("\nFinal DataFrame Columns:")
        print(final_summary_df.columns)
        
        final_summary_df.to_parquet(OUTPUT_PATH, engine='pyarrow', index=False)
        build_indus_bridge(final_summary_df, config.ECHA_INDUS_OUTPUT_PATH)

        print("\n--- Success! ---")
        print(f"Processing finished. Summary saved to {OUTPUT_PATH}")
        print("\nOutput DataFrame preview (first 5 rows):")
        
        # Set display options to show all columns
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(final_summary_df.head())

    except ImportError:
        print("\n--- Error ---", file=sys.stderr)
        print("Required libraries (pandas or pyarrow) not found.", file=sys.stderr)
        print("Please install them using: pip install pandas pyarrow", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n--- Error ---", file=sys.stderr)
        print(f"Input file not found at: {INPUT_PATH}", file=sys.stderr)
        print("Please check the INPUT_PATH variable in the script.", file=sys.stderr)
        sys.exit(1)
    except KeyError as e:
        print(f"\n--- Error ---", file=sys.stderr)
        print(f"Missing expected column(s) in input file.", file=sys.stderr)
        print(f"Details: {e}", file=sys.stderr)
        print(f"Please ensure {REQUIRED_COLS} exist.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n--- An unexpected error occurred ---", file=sys.stderr)
        print(f"Error details: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
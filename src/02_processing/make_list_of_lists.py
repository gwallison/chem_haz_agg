import pandas as pd
from functools import reduce
import os
import config

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================
# Define all your data sources in this list.
# - 'name': The name of the list/regulation (will become a column in the final table).
# - 'path': The file path to the data source.
# - 'format': The file format ('csv' or 'excel').
# - 'casrn_col': The name of the column containing the CASRN in this specific file.
#
# Add a dictionary for each of your files to this list.

DATA_SOURCES = [
    {
        'name': 'CleanWaterAct',
        'path': 'C:/MyDocs/integrated/chem_profiles/data/01_raw/Chemical_List_CWA311HS-2022-03-31.csv',
        'format': 'csv',
        'casrn_col': 'CASRN'
    },
    {
        'name': 'TEDX',
        'path': 'C:/MyDocs/integrated/chem_profiles/data/01_raw/TEDX_EDC_trimmed.xls',
        'format': 'excel',
        'casrn_col': 'CAS_Num'
    },
    {
        'name': 'Prop65',
        'path': r"C:\MyDocs\integrated\chem_profiles\data\01_raw\p65list12182020.csv",
        'format': 'csv',
        'casrn_col': 'CAS No.',
        'encoding': 'latin1'  

    },
    # Add other data sources here following the same structure
]

# ==============================================================================
# 2. PROCESSING ENGINE
# ==============================================================================

def load_and_standardize_source(source_config):
    """
    Loads a single data source, standardizes its CASRN column, and creates
    a new column to indicate presence on that source's list.

    Args:
        source_config (dict): A dictionary from the DATA_SOURCES list.

    Returns:
        pandas.DataFrame: A standardized DataFrame with 'CASRN' and a boolean
                          column for the list, or None if the file is not found.
    """
    file_path = source_config['path']
    list_name = source_config['name']
    casrn_col = source_config['casrn_col']
    file_format = source_config['format']

    if not os.path.exists(file_path):
        print(f"Warning: File not found at '{file_path}'. Skipping this source.")
        return None

    print(f"Processing '{list_name}' from '{file_path}'...")

    try:
        if file_format == 'csv':
            encoding = source_config.get('encoding', 'utf-8')
            df = pd.read_csv(file_path, dtype=str, 
                             encoding=encoding)
        elif file_format == 'excel':
            df = pd.read_excel(file_path, dtype=str)
        else:
            print(f"Warning: Unsupported file format '{file_format}' for {list_name}. Skipping.")
            return None

        # Check if the specified CASRN column exists
        if casrn_col not in df.columns:
            print(f"Warning: CASRN column '{casrn_col}' not found in '{file_path}'. Skipping.")
            return None

        # Standardize the DataFrame
        # 1. Rename the source's CASRN column to a standard name 'CASRN'
        df.rename(columns={casrn_col: 'CASRN'}, inplace=True)

        # 2. Create a new column for this list, marking all entries as True
        df[list_name] = True
        
        # 3. Keep only the essential columns: 'CASRN' and the new list column
        standardized_df = df[['CASRN', list_name]].copy()

        # 4. Drop any rows with missing CASRNs and remove duplicates
        standardized_df.dropna(subset=['CASRN'], inplace=True)
        standardized_df.drop_duplicates(subset=['CASRN'], inplace=True)
        
        return standardized_df

    except Exception as e:
        print(f"Error processing file '{file_path}': {e}")
        return None


# --- Main script execution ---

# A list to hold all the processed DataFrames
all_dfs = []

# Loop through the configuration and process each file
for source in DATA_SOURCES:
    processed_df = load_and_standardize_source(source)
    if processed_df is not None:
        all_dfs.append(processed_df)

# Check if any data was successfully processed
if not all_dfs:
    print("No data sources were processed successfully. Exiting.")
    # Exit or raise an error as appropriate for your workflow
else:
    # Merge all the DataFrames together using an outer join.
    # An outer join ensures that a chemical from any list is included in the final result.
    # The 'reduce' function iteratively applies the merge operation to the list of DataFrames.
    final_df = reduce(lambda left, right: pd.merge(left, right, on='CASRN', how='outer'), all_dfs)

    # Set the CASRN as the index for the final DataFrame
    final_df.set_index('CASRN', inplace=True)

    # The merge operation will create NaN for chemicals not on a particular list.
    # Replace these NaN values with False for clarity.
    final_df = final_df.fillna(False)

    print("\n--- Data Consolidation Complete ---")
    print(f"Successfully merged {len(all_dfs)} data sources.")
    print(f"Final DataFrame contains {final_df.shape[0]} unique chemicals.")


# ==============================================================================
# 3. EXAMPLE USAGE
# ==============================================================================

# This block will only run if data was processed
if 'final_df' in locals():
    print("\n--- Final DataFrame Preview ---")
    print(final_df.head())

    # --- How to use the final DataFrame ---

    # Check if a specific chemical (by CASRN) is on any list
    casrn_to_check = '75-07-0' # Example: Acetaldehyde
    if casrn_to_check in final_df.index:
        print(f"\nStatus for CASRN {casrn_to_check}:")
        print(final_df.loc[casrn_to_check])
    else:
        print(f"\nCASRN {casrn_to_check} not found in any list.")

    # Get a list of all chemicals on the 'CWA' list
    CWA_chemicals = final_df[final_df['CleanWaterAct'] == True]
    print(f"\nFound {len(CWA_chemicals)} chemicals on the CWA list.")
    print(CWA_chemicals.head())

    # Save the final consolidated DataFrame to a CSV file
    outdir = r"C:/MyDocs/integrated/chem_profiles/data/02_intermediate"
    
    final_df.to_parquet(os.path.join(outdir,'list_of_lists.parquet'))
    
    print("\nFinal DataFrame saved to 'list_of_lists.csv'")
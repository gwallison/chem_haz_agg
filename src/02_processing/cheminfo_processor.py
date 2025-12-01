import os
import pandas as pd
import warnings
import numpy as np # Added for the new function
import config

# --- 1. Standardized Project Paths ---
# from master_list_manager import MASTER_FILE_PATH
CHEMINFO_REF_DIR = config.CHEMINFO_REF_DIR 
CHEMINFO_SDF_OUTPUT_PATH = config.CHEMINFO_SDF_OUTPUT_PATH
CHEMINFO_HAZARD_OUTPUT_PATH = config.CHEMINFO_HAZARD_OUTPUT_PATH
# New path for the summarized hazard data
CHEMINFO_HAZARD_SUMMARY_PATH = config.CHEMINFO_HAZARD_SUMMARY_PATH


# --- 2. SDF (Structure-Data File) Processing (Unchanged) ---
class SdfParser:
    # ... (class code is unchanged)
    def __init__(self, filepath):
        self.filepath = filepath
        with open(filepath, 'r') as f:
            self.lines = f.read().splitlines()
        self.all_records = []
        self.all_varnames = self._get_all_varnames()
    def _get_all_varnames(self):
        names = set()
        for line in self.lines:
            if line.startswith('> <'):
                names.add(line[3:-1])
        return list(names)
    def parse_records(self):
        record = {}
        for line in self.lines:
            if line.startswith('> <'):
                current_var = line[3:-1]
                record[current_var] = self.lines[self.lines.index(line) + 1].strip()
            elif line == '$$$$':
                self.all_records.append(record)
                record = {}
        return pd.DataFrame(self.all_records)

def process_sdf_files(source_dir: str, output_path: str):
    # ... (function is unchanged)
    print(f"--- Processing SDF files in {source_dir} ---")
    sdf_files = [os.path.join(source_dir, fn) for fn in os.listdir(source_dir)
                 if fn.startswith('hazard') and fn.endswith('.sdf')]
    if not sdf_files:
        print("No 'hazard*.sdf' files found.")
        return
    all_dfs = []
    for filepath in sdf_files:
        print(f"  - Parsing {os.path.basename(filepath)}")
        parser = SdfParser(filepath)
        df = parser.parse_records()
        all_dfs.append(df)
    if not all_dfs:
        print("No data could be extracted from SDF files.")
        return
    combined_df = pd.concat(all_dfs, ignore_index=True)
    final_df = combined_df.drop_duplicates(subset=['DTXSID'])
    final_df.to_parquet(output_path, index=False)
    print(f"✅ SDF processing complete. Saved {len(final_df)} records to {output_path}")


# --- 3. XLSX (Excel Hazard File) Processing ---

def get_summary_from_xls(filepath: str) -> pd.DataFrame:
    """Reads a single ChemInformatics hazard Excel file."""
    cols = ['DTXSID','CASRN','Name','SMILES','HH: Oral','HH: Inhalation','HH: Dermal','HH: Carcinogenicity',
            'HH: Genotoxicity Mutagenicity','HH: Endocrine Disruption','HH: Reproductive','HH: Developmental',
            'HH: Neurotoxicity: Repeat Exposure','HH: Neurotoxicity: Single Exposure',
            'HH: Systemic Toxicity: Repeat Exposure','HH: Systemic Toxicity: Single Exposure',
            'HH: Skin Sensitization','HH: Skin Irritation','HH: Eye Irritation',
            'Ecotoxicity: Acute Aquatic Toxicity','Ecotoxicity: Chronic Aquatic Toxicity',
            'Fate: Persistence','Fate: Bioaccumulation','Fate: Exposure']
    
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        df = pd.read_excel(filepath, skiprows=5, engine='openpyxl')
    
    df.columns = cols
    # MODIFIED: Clean up column names by removing prefixes and spaces
    df = df.drop(columns='SMILES')
    df.columns = [col.replace('HH: ', '').replace('Ecotoxicity: ', '').replace('Fate: ', '').replace(' ', '_')
                  for col in df.columns]
    return df

def process_hazard_xlsx_files(source_dir=CHEMINFO_REF_DIR, 
                              output_path=CHEMINFO_HAZARD_OUTPUT_PATH):
    """
    Finds and processes all 'haza*.xlsx' files in a directory, combines them,
    and saves the result as a Parquet file.
    """
    # ... (function is unchanged internally, but benefits from cleaned columns from the function above)
    print(f"\n--- Processing Hazard XLSX files in {source_dir} ---")
    xlsx_files = [os.path.join(source_dir, fn) for fn in os.listdir(source_dir)
                  if fn.startswith('haza') and fn.endswith('.xlsx')]
    if not xlsx_files:
        print("No 'haza*.xlsx' files found.")
        return
    all_dfs = []
    for filepath in xlsx_files:
        print(f"  - Parsing {os.path.basename(filepath)}")
        try:
            all_dfs.append(get_summary_from_xls(filepath))
            # tmp = all_dfs[-1]
            # print(f'len of water search: {tmp[tmp.CASRN=="7732-18-5"]}')
        except Exception as e:
            print(f"    -> Could not process {os.path.basename(filepath)}. Error: {e}")
    if not all_dfs:
        print("No data could be extracted from XLSX files.")
        return
    combined_df = pd.concat(all_dfs, ignore_index=True)
    # print(combined_df.columns)
    # final_df = combined_df.drop_duplicates(subset=['DTXSID'])
    final_df = combined_df.drop_duplicates(subset=['CASRN'])
    final_df.to_parquet(output_path, index=False)
    print(f"✅ XLSX processing complete. Saved {len(final_df)} records to {output_path}")
    return final_df


# --- 4. NEW: Hazard Summary Function ---

def summarize_hazard_data(
    hazard_df: pd.DataFrame,
    output_path: str,
    categories: list = ['Carcinogenicity', 'Genotoxicity_Mutagenicity', 
                        'Reproductive']
) -> pd.DataFrame:
    """
    Summarizes EPA hazard codes from specific categories into a single code ('tox', 'lo', 'unk').

    Args:
        hazard_df (pd.DataFrame): The input DataFrame from process_hazard_xlsx_files.
        output_path (str): The path to save the summarized Parquet file.
        categories (list): A list of hazard columns to consider for the summary.

    Returns:
        pd.DataFrame: A DataFrame with CASRN and the new summary code.
    """
    print("\n--- Summarizing ChemInformatics Hazard Codes ---")
    
    # Check if all requested categories are in the DataFrame
    missing_cats = [cat for cat in categories if cat not in hazard_df.columns]
    if missing_cats:
        print(f"❌ Error: The following categories were not found in the DataFrame: {missing_cats}")
        return

    # Create a temporary DataFrame with just the categories of interest
    summary_df = hazard_df[['CASRN'] + categories].copy()
    
    # Define the mapping from EPA codes to our summary codes
    code_map = {'VH': 'tox', 'H': 'tox', 'M': 'lo', 'L': 'lo', 'I': 'unk', 'ND': 'unk'}
    
    # Apply the mapping to all category columns at once
    for cat in categories:
        summary_df[cat] = summary_df[cat].map(code_map).fillna('unk')
        
    # Use numpy.select for efficient, conditional logic to create the final code
    conditions = [
        (summary_df[categories] == 'tox').any(axis=1),
        (summary_df[categories] == 'unk').any(axis=1)
    ]
    choices = ['tox', 'unk']
    
    summary_df['hazard_summary_code'] = np.select(conditions, choices, default='lo')
    
    # Prepare the final output DataFrame
    final_df = summary_df[['CASRN', 'hazard_summary_code']]
    final_df.to_parquet(output_path, index=False)
    print(f"✅ Hazard summary complete. Saved {len(final_df)} records to {output_path}")
    
    return final_df


# --- 5. Main Execution Block ---
if __name__ == '__main__':
    os.makedirs(CHEMINFO_REF_DIR, exist_ok=True)
    
    # == STEP 1: Process the raw hazard Excel files ==
    hazard_data = process_hazard_xlsx_files(
        source_dir=CHEMINFO_REF_DIR,
        output_path=CHEMINFO_HAZARD_OUTPUT_PATH
    )
    # print(hazard_data.columns)
    # == STEP 2: If Step 1 was successful, create the hazard summary ==
    if hazard_data is not None:
        summary = summarize_hazard_data(
            hazard_df=hazard_data,
            output_path=CHEMINFO_HAZARD_SUMMARY_PATH
        )
        if summary is not None:
            print("\n--- Hazard Summary Preview ---")
            print(summary.head(10))
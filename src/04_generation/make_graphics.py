import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import pandas as pd

# --- Reusable Color Map ---
TIER_COLOR_MAP = {
    1: 'red',
    2: '#FFC300', # A yellowish orange
    3: 'lime',
    4: 'gray'
}



def create_tier_graphic(
    data: dict,
    label_positions: list[tuple[str, int, int]] = None,
#    filename: str = 'tier_graphic.png', 
    filename: str = 'tier_graphic.svg', 
    output_dir: str = r"C:\MyDocs\integrated\chem_profiles_old\code\tmp\tier_fig_sm"
):
    """
    Generates a graphic with squares based on input data and explicitly defined positions.

    Args:
        data (dict): A dictionary where keys are square labels and values are integers for coloring.
        label_positions (list[tuple[str, int, int]], optional): A list of tuples, where each tuple
            is (label_string, row_index, col_index).
            row_index: 0 for top row, 1 for bottom row.
            col_index: 0 to 3 for columns from left to right.
            If None, squares will be placed in default top-left to bottom-right order
            up to 8 squares, using dictionary insertion order for labels.
        filename (str, optional): The name of the output file.
        output_dir (str, optional): The directory to save the file in.
    """
    # 1. Setup the plot
    # fig, ax = plt.subplots(figsize=(8, 3), dpi=150)
    fig, ax = plt.subplots(figsize=(4, 1.5), dpi=50)
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 3)
    ax.axis('off')

    # 2. Draw the large "Tier" square
    tier_value = data.get('Tier', 4)
    tier_color = TIER_COLOR_MAP.get(tier_value, 'gray')
    tier_square = patches.Rectangle((0.25, 0.25), 2.5, 2.5, facecolor=tier_color)
    ax.add_patch(tier_square)
    
    # --- NEW: Define the descriptive text for each tier ---
    tier_text_map = {
        1: "Tier 1:\n\nKnown\nHazard",
        2: "Tier 2:\n\nTreat as\nHazard",
        3: "Tier 3:\n\nLow Hazard",
        4: "Tier 4:\n\nHazard\nUnknown"
    }
    # Use .get() to retrieve the text, with a fallback for any unexpected tier values
    tier_label = tier_text_map.get(tier_value, f"Tier {tier_value}")

    # --- MODIFIED: Use the new label and adjusted font size ---
    ax.text(1.5, 1.5, tier_label, color='black', ha='center', va='center', fontsize=8, weight='bold')

    # 3. Define and draw the small squares (This section is unchanged)
    start_x = 3.0
    start_y_row0 = 1.75
    start_y_row1 = 0.25
    square_dim = 1.0
    col_spacing = 0.2
    
    def get_pixel_coords(row_idx, col_idx):
        x = start_x + col_idx * (square_dim + col_spacing)
        y = start_y_row0 if row_idx == 0 else start_y_row1
        return x, y

    if label_positions is None:
        default_labels = [key for key in data.keys() if key != 'Tier']
        generated_label_positions = []
        for i, label in enumerate(default_labels):
            if i >= 8:
                break
            row = i // 4
            col = i % 4
            generated_label_positions.append((label, row, col))
        labels_to_plot = generated_label_positions
    else:
        labels_to_plot = label_positions

    for item in labels_to_plot:
        label, row_idx, col_idx = item
        if label not in data:
            print(f"Warning: Label '{label}' not found in data dictionary. Skipping.")
            continue
        x, y = get_pixel_coords(row_idx, col_idx)
        value = data.get(label, 4)
        color = TIER_COLOR_MAP.get(value, 'gray')
        square = patches.Rectangle((x, y), square_dim, square_dim, facecolor=color)
        ax.add_patch(square)
        ax.text(x + square_dim/2, y + square_dim/2, label, 
                color='black', ha='center', va='center', fontsize=8, weight='bold')

    # 4. Save the final graphic (unchanged)
    os.makedirs(output_dir, exist_ok=True)
    full_path = os.path.join(output_dir, filename)
    plt.savefig(full_path, bbox_inches='tight', pad_inches=0.1, facecolor='black')
    plt.close(fig)
    print(f"✅ Successfully created '{full_path}'")
# (The create_color_square function is omitted for brevity but is still part of the script)
# ...

# --- Example Usage for the New Dynamic Positioning ---
if __name__ == '__main__':
    import random
    # # Data for the squares
    # graphic_data = {
    #     'Tier': 1,
    #     'A': 1, 'B': 2, 'C': 3,
    #     'E': 1, 'G': 3, 'H': 4
    # }

    # Example 1: Custom positions matching your attached figure
    print("--- Generating graphic with specific custom positions ---")
    custom_positions = [
        ('CMR', 0, 1), # Label A in Top Row, Column 0 (first column)
        # ('B', 0, 1), # Label B in Top Row, Column 1 (second column)
        ('EDC', 0, 2), # Label C in Top Row, Column 3 (fourth column)
        #('E', 1, 0), # Label E in Bottom Row, Column 0
        ('ENV', 0, 3), # Label G in Bottom Row, Column 2
        #('H', 1, 3)  # Label H in Bottom Row, Column 3
    ]
    
    tierfn = r"C:\MyDocs\integrated\chem_profiles_old\code\data\final_tier_classifications.parquet"
    tierdf = pd.read_parquet(tierfn)
    tierdf['CMR'] = tierdf.CMR_Tier.str[-1].astype('int')
    tierdf['EDC'] = tierdf.EDC_Tier.str[-1].astype('int')
    tierdf['ENV'] = tierdf.ENV_Tier.str[-1].astype('int')
    # tierdf = tierdf.replace('Tier ','')
    # print(tierdf.head())
    for i,row in tierdf.iterrows():
        print(row)
        tierval = min([row.CMR,row.ENV,row.EDC])
        if tierval == 3:
            if max([row.CMR,row.ENV,row.EDC])==4:
                tierval = 4
        graphic_data = {'Tier': tierval,
                        'CMR': row.CMR,
                        'ENV': row.ENV,
                        'EDC': row.EDC}
    
    
    
        create_tier_graphic(graphic_data, 
                            label_positions=custom_positions, 
                            filename=f'{row.CASRN}.svg')
    

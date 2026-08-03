import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
import sys
import pandas as pd

# Add the project root to the Python path to resolve the 'config' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import config
from config import FINAL_TIERED_OUTPUT_PATH

# --- Reusable Color Map ---
TIER_COLOR_MAP = {
    1: 'red',
    2: '#FFC300', # A yellowish orange
    3: 'dodgerblue',
    4: 'darkgray'
}


def create_tier_graphic(
    data: dict,
    label_positions: list[tuple[str, int, int]] = None,
    filename: str = 'tier_graphic.svg',
    output_dir: str = None,
):
    """
    Generates a graphic with squares based on input data and explicitly defined positions.
    Adds unique 'gid' attributes to squares for web interactivity.
    """
    if output_dir is None:
        output_dir = os.path.join(config.DOCS_DIR, 'images')

    # 1. Setup the plot (Unchanged)
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
    
    # MODIFIED: Add a unique and predictable 'gid' to the main tier box.
    tier_square.set_gid("overall_tier_box")
    
    ax.add_patch(tier_square)
    
    tier_text_map = {
        1: "Tier 1:\n\nKnown\nHazard",
        2: "Tier 2:\n\nTreat as\nHazard",
        3: "Tier 3:\n\nLow Hazard",
        4: "Tier 4:\n\nHazard\nUnknown"
    }
    tier_label = tier_text_map.get(tier_value, f"Tier {tier_value}")
    ax.text(1.5, 1.5, tier_label, color='black', ha='center', va='center', fontsize=8, weight='bold')

    # 3. Define and draw the small squares
    start_x = 3.0
    start_y_row0 = 1.75
    start_y_row1 = 0.25
    square_dim = 1.0
    col_spacing = 0.2
    
    def get_pixel_coords(row_idx, col_idx):
        x = start_x + col_idx * (square_dim + col_spacing)
        y = start_y_row0 if row_idx == 0 else start_y_row1
        return x, y

    labels_to_plot = label_positions if label_positions is not None else []
    # (Simplified the logic slightly as the default case was not used in your example)

    for item in labels_to_plot:
        label, row_idx, col_idx = item
        if label not in data:
            print(f"Warning: Label '{label}' not found in data dictionary. Skipping.")
            continue
        x, y = get_pixel_coords(row_idx, col_idx)
        value = data.get(label, 4)
        color = TIER_COLOR_MAP.get(value, 'gray')
        square = patches.Rectangle((x, y), square_dim, square_dim, facecolor=color)
        
        # MODIFIED: Add a unique 'gid' based on the hazard label (e.g., 'cmr_box').
        square.set_gid(f"{label.lower()}_box")
        
        ax.add_patch(square)
        ax.text(x + square_dim/2, y + square_dim/2, label, 
                color='black', ha='center', va='center', fontsize=8, weight='bold')

    # 4. Save the final graphic (Unchanged)
    os.makedirs(output_dir, exist_ok=True)
    full_path = os.path.join(output_dir, filename)
    plt.savefig(full_path, bbox_inches='tight', pad_inches=0.1, facecolor='black')
    plt.close(fig)
    print(f"✅ Successfully created '{full_path}' with interactive IDs.")



def generate_all_tier_graphics(output_dir: str = None, casrns: list = None):
    """
    Regenerates the per-CASRN tier SVG for every chemical in the final
    tiered classification output. If casrns is given, only those CASRNs
    are regenerated instead of the full set.
    """
    custom_positions = [
        ('CMR', 1, 0),
        ('EDC', 1, 1),
        ('ENV', 1, 3),
        ('IHL', 0, 0),
        ('ORL', 0, 1),
        ('SKN', 0, 2),
        ('OGN', 0, 3),
    ]

    tierdf = pd.read_parquet(FINAL_TIERED_OUTPUT_PATH)
    if casrns is not None:
        tierdf = tierdf[tierdf.CASRN.isin(casrns)]
    tierdf['CMR'] = tierdf.CMR_Tier.str[-1].astype('int')
    tierdf['EDC'] = tierdf.EDC_Tier.str[-1].astype('int')
    tierdf['ENV'] = tierdf.ENV_Tier.str[-1].astype('int')
    tierdf['IHL'] = tierdf.IHL_Tier.str[-1].astype('int')
    tierdf['ORL'] = tierdf.ORL_Tier.str[-1].astype('int')
    tierdf['SKN'] = tierdf.SKN_Tier.str[-1].astype('int')
    tierdf['OGN'] = tierdf.OGN_Tier.str[-1].astype('int')

    for i, row in tierdf.iterrows():
        tierval = min([row.CMR, row.ENV, row.EDC, row.IHL, row.ORL, row.SKN, row.OGN])
        if tierval == 3:
            if max([row.CMR, row.ENV, row.EDC, row.IHL, row.ORL, row.SKN, row.OGN]) == 4:
                tierval = 4
        graphic_data = {'Tier': tierval,
                        'CMR': row.CMR,
                        'ENV': row.ENV,
                        'EDC': row.EDC,
                        'IHL': row.IHL,
                        'ORL': row.ORL,
                        'SKN': row.SKN,
                        'OGN': row.OGN,
                        }

        create_tier_graphic(graphic_data,
                            label_positions=custom_positions,
                            filename=f'{row.CASRN}.svg',
                            output_dir=output_dir)


if __name__ == '__main__':
    print("--- Generating graphic with specific custom positions ---")
    generate_all_tier_graphics()


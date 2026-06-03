# Open-FF Chemical Hazard Aggregator (chem_haz_agg)

The **Open-FF Chemical Hazard Aggregator** is a data aggregation, normalization, and visualization tool built to make environmental and chemical hazard information accessible to researchers, advocates, health professionals, and the public. It focuses on cataloging substances appearing in hydraulic fracturing and petrochemical operations.

This project is developed by **[Open-FF](https://open-ff.org/)** and sponsored by **[The FracTracker Alliance](https://www.fractracker.org/)**.

---

## Key Features

1.  ** Authoritative Source Normalization**: Aggregates toxicology records from 10+ registries, including ECHA, EPA CompTox, EPA IRIS, ATSDR, NJ RTK, CAMEO, OECD, and CA Prop 65.
2.  **Four-Tier Summary System**: Simplifies complex regulatory listings into intuitive hazard classes (CMR, EDC, ENV, IHL, ORL, SKN, OGN) across four tiers:
    *   🟥 **Tier 1 (Known Hazards)**: GHS Category 1/2 classifications or "Danger" signal words.
    *   🟧 **Tier 2 (Emerging Concerns)**: Regulatory watchlists, computer models (QSAR), or scientific literature.
    *   🟦 **Tier 3 (Low/Moderate Hazards)**: Favorable safety profile confirmed by direct toxicity studies.
    *   ⬜ **Tier 4 (Data Deficient)**: Lacking public toxicity data. *Absence of evidence is not evidence of safety.*
3.  **Modern Web Interface**: Built on MkDocs Material, featuring dynamic data search/filtering, interactive reference badges, Lato typography, and custom light/dark design theme layouts.
4.  **Clickable Visual Summaries**: A fully searchable index table where clicking on the CASRN or the visual Tier graphic routes users to detailed, chemical-specific profile pages.

---

## Project Structure

```
├── config.py                 # Core path configuration and registry definitions
├── master_list_manager.py    # Master CASRN identity mapping tool
├── LICENSE                   # MIT License
├── README.md                 # Project README
├── data/
│   ├── 01_raw/               # Raw registry source data (ignored; local cache)
│   ├── 02_intermediate/      # Temporary processing parquets (ignored)
│   └── 03_processed/         # Final normalized Parquets and Gemini LLM text cache (tracked)
├── src/                      # Data pipeline source code
│   ├── 01_collection/        # API scrapers and harvesters
│   ├── 02_processing/        # Normalization and list building
│   ├── 03_integration/       # GHS classification and tier mapping
│   └── 04_generation/        # Markdown generation and site build logic
└── mkdocs/                   # MkDocs project root
    ├── mkdocs.yml            # MkDocs site configuration and navigation
    └── docs/                 # Documentation source content and assets
```

---

## Setup & Running

### 1. Installation
Install Python dependencies (Python 3.8+ recommended):
```bash
pip install pandas pyarrow itables mkdocs-material pymdown-extensions
```

### 2. Running Site Generation
To generate the summary tables and chemical profile pages, run the build script from the repository root:

*   **Developer Mode (Fast Preview - Recommended for local changes)**:
    Clears the output folder and generates exactly 10 chemical pages for near-instant rendering.
    ```bash
    python src/04_generation/build_site.py --dev
    ```

*   **Full Production Mode**:
    Generates the entire chemical catalog (3000+ pages).
    ```bash
    python src/04_generation/build_site.py
    ```

### 3. Local Web Server Preview
Start the local MkDocs web server to preview changes:
```bash
cd mkdocs
mkdocs serve
```
Open `http://127.0.0.1:8000` in your web browser.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

from dataclasses import dataclass, field
from pathlib import Path
import os

PROJECT_ROOT = str(Path(__file__).parent.parent)
SCRAPE_PYTHON = r"C:\Users\Gary\anaconda3\envs\scrape\python.exe"


@dataclass
class Step:
    id: str
    name: str
    category: str       # "AUTO" | "MANUAL-FETCH" | "HUMAN-LOOP" | "BLOCKED"
    stage: str
    description: str
    instructions: str = ""
    url: str = ""
    cmd: list = field(default_factory=list)
    use_scrape_env: bool = False
    extra_env: dict = field(default_factory=dict)
    cwd: str = ""       # relative to PROJECT_ROOT; "" = PROJECT_ROOT
    dependencies: list = field(default_factory=list)

    def resolved_cmd(self):
        if not self.cmd:
            return []
        cmd = list(self.cmd)
        if self.use_scrape_env and cmd[0] == "python":
            cmd[0] = SCRAPE_PYTHON
        return cmd

    def resolved_env(self):
        env = os.environ.copy()
        env.update(self.extra_env)
        return env

    def resolved_cwd(self):
        if self.cwd:
            return str(Path(PROJECT_ROOT) / self.cwd)
        return PROJECT_ROOT


STEPS = [
    # ── Gateway — Master List Update ──────────────────────────────────────────
    Step(
        id="gateway-fracfocus",
        name="Add CASRNs from FracFocus",
        category="AUTO",
        stage="Gateway — Master List Update",
        description=(
            "Add any new CASRNs surfaced by the latest FracFocus working_df. "
            "Skip if FracFocus data has not been updated since the last refresh."
        ),
        cmd=["python", "master_list_manager.py", "add-fracfocus"],
    ),
    Step(
        id="gateway-build-nb",
        name="Add CASRNs from Open-FF build",
        category="AUTO",
        stage="Gateway — Master List Update",
        description=(
            "Add CASRNs newly surfaced by the Open-FF build notebook. "
            "Skip if no new Open-FF build has been run since the last refresh."
        ),
        cmd=["python", "master_list_manager.py", "add-build-nb"],
    ),
    Step(
        id="gateway-add-file",
        name="Add CASRNs from a custom file",
        category="HUMAN-LOOP",
        stage="Gateway — Master List Update",
        description=(
            "Add CASRNs from any other one-off source (CSV or parquet). "
            "Skip if no additional sources are needed this cycle."
        ),
        instructions=(
            "Run from the project root, substituting your file path:\n\n"
            "```\n"
            "python master_list_manager.py add-file <path/to/file.csv>\n"
            "```\n\n"
            "The file must contain a `CASRN` column. "
            "Accepts `.csv` or `.parquet`. "
            "Skipped and quarantined CASRNs are logged automatically.\n\n"
            "Skip if no additional file sources are needed this cycle."
        ),
    ),

    # ── Preparation ───────────────────────────────────────────────────────────
    Step(
        id="prep-summary",
        name="Master List Summary",
        category="AUTO",
        stage="Preparation",
        description="Confirm master list state and that temp_casrn_list.csv is current.",
        cmd=["python", "master_list_manager.py", "summary"],
    ),

    # ── Manual Fetches ────────────────────────────────────────────────────────
    Step(
        id="fetch-tsca",
        name="TSCA Inventory",
        category="MANUAL-FETCH",
        stage="Manual Fetches",
        description="Download updated TSCA non-confidential inventory if newer than current file.",
        url="https://www.epa.gov/tsca-inventory/how-access-tsca-inventory#download",
        instructions=(
            "1. Check the 'last updated' date for the non-confidential inventory "
            "(current saved: `TSCAINV_072025.csv`).\n"
            "2. If newer, download the CSV ZIP, unzip, and move `TSCAINV_XXXXXX.csv` "
            "to `data/01_raw/`.\n"
            "3. Update `config.TSCA_RAW_CSV` in `config.py` to match the new filename.\n\n"
            "If the current file is already up to date, click **Skip**."
        ),
    ),
    Step(
        id="fetch-epa1",
        name="EPA 1 — CompTox DTXSID Batch",
        category="MANUAL-FETCH",
        stage="Manual Fetches",
        description="Download CASRN→DTXSID mapping from CompTox batch search.",
        url="https://comptox.epa.gov/dashboard/batch-search",
        instructions=(
            "1. Open `data/01_raw/temp_casrn_list.csv` and copy the CASRN column.\n"
            "2. Paste into 'ENTER Identifiers to Search' on the CompTox batch search page.\n"
            "3. Download the results file and move `CCD-Batch-Search_*.csv` to `data/01_raw/`."
        ),
    ),
    Step(
        id="fetch-epa3",
        name="EPA 3 — ChemInformatics",
        category="MANUAL-FETCH",
        stage="Manual Fetches",
        description="Collect hazard and GHS data from EPA ChemInformatics (~7 passes of 500 CASRNs).",
        url="https://hcd.rtpnc.epa.gov/#/",
        instructions=(
            "**Full refresh:** Move existing `data/01_raw/ChemInfo_ref_files/` contents "
            "to its `old/` subdirectory first.\n\n"
            "**For each ~500-CASRN chunk** from `temp_casrn_list.csv`:\n"
            "1. Click **Hazard** module → magnifying glass icon\n"
            "2. **Search by identifiers** tab → paste CASRNs → Search\n"
            "3. When results appear, click **Cart +** to add to cart\n"
            "4. Click **Cart** icon → generate report (takes a few minutes)\n"
            "5. Export to XLSX → move to `ChemInfo_ref_files/` (`safety*.xlsx`)\n"
            "6. Export to SDF → move to `ChemInfo_ref_files/`\n"
            "7. Click **SAFETY** module → safety glasses icon\n"
            "8. Click **Cart** again → generate second report for the same CASRNs\n"
            "9. Export to XLSX → move to `ChemInfo_ref_files/` (`haza*.xlsx`)\n\n"
            "Repeat for all ~7 chunks (~3,221 CASRNs total). Mark done when all chunks complete."
        ),
    ),
    Step(
        id="fetch-epa-lists",
        name="EPA List of Lists",
        category="MANUAL-FETCH",
        stage="Manual Fetches",
        description="Export list membership data from CompTox batch search.",
        url="https://comptox.epa.gov/dashboard/batch-search",
        instructions=(
            "1. Paste `temp_casrn_list.csv` contents into CompTox batch search "
            "with **all lists selected**.\n"
            "2. Download the resulting Excel sheet.\n"
            "3. Save as `data/01_raw/epa_lists.xlsx`."
        ),
    ),
    Step(
        id="fetch-prop65",
        name="PROP 65",
        category="MANUAL-FETCH",
        stage="Manual Fetches",
        description="Download California PROP 65 list if newer than Jan 2025.",
        url="https://oehha.ca.gov/proposition-65/proposition-65-list",
        instructions=(
            "1. Compare the dates for the 'Documents' on the website with the "
            "latest saved version in RAW.\n"
            "2. If newer, download the CSV.\n"
            "3. Remove the header row so column names are the first row.\n"
            "4. Save as `data/01_raw/prop65_YYYY_MM.csv`.\n"
            "5. Update `config.PROP65_RAW` in `config.py` to match the new filename.\n\n"
            "If current file is already up to date, click **Skip**."
        ),
    ),
    Step(
        id="fetch-echa1",
        name="ECHA 1 — Harmonised List",
        category="MANUAL-FETCH",
        stage="Manual Fetches",
        description="Export the ECHA Harmonised Classification list.",
        url="https://chem.echa.europa.eu/obligation-lists/clhList",
        instructions=(
            "**Caution:** ECHA system has been in flux — verify the export UI works "
            "before proceeding.\n\n"
            "1. Export the list as Excel from the clhList UI.\n"
            "2. Save as `Harmonised_List_*.xlsx` in `data/01_raw/`.\n\n"
            "Script auto-selects the most recent matching file — no `config.py` edit needed."
        ),
    ),
    Step(
        id="fetch-japan",
        name="Japan NITE GHS",
        category="MANUAL-FETCH",
        stage="Manual Fetches",
        description="Download the Japan NITE GHS classification database.",
        url="https://www.chem-info.nite.go.jp/chem/english/ghs/ghs_nite_download_e.html",
        instructions=(
            "**Download link:** https://www.chem-info.nite.go.jp/chem/english/ghs/files/list_nite_all_e.xlsx\n\n"
            "1. Download the most recent English classification file.\n"
            "2. Save as `data/01_raw/list_nite_all_e.xlsx`."
        ),
    ),
    Step(
        id="fetch-australia",
        name="Australia Safe Work GHS",
        category="MANUAL-FETCH",
        stage="Manual Fetches",
        description="Download Safe Work Australia hazardous chemicals database.",
        url="https://hcis.safeworkaustralia.gov.au/",
        instructions=(
            "1. On the landing page, click the link to download the Excel sheet.\n"
            "2. The downloaded file will be named like "
            "`HCIS_Chemical_Data_YYYY-MM-DD.xlsx`.\n"
            "3. Move it to `data/01_raw/` (keep the original filename).\n\n"
            "Script auto-selects the most recent matching file — no `config.py` edit needed."
        ),
    ),
    Step(
        id="fetch-iris",
        name="IRIS A-to-Z List",
        category="MANUAL-FETCH",
        stage="Manual Fetches",
        description="Download the EPA IRIS chemical list if count exceeds current 572.",
        url="https://iris.epa.gov/AtoZ/?list_type=alpha",
        instructions=(
            "1. Check the total count on the IRIS A-to-Z page (current: 572).\n"
            "2. If higher, download the Excel file.\n"
            "3. Save as `data/01_raw/simple_list_alpha.xlsx`.\n\n"
            "If count unchanged, click **Skip**."
        ),
    ),
    Step(
        id="scifinder",
        name="SciFinder",
        category="HUMAN-LOOP",
        stage="Manual Fetches",
        description="Run SciFinder extractor — requires 2 manual login pauses.",
        instructions=(
            "Run `src/01_collection/SciFinder_extractor.py` functions in order:\n"
            "1. `update_from_master_list()` — requires OSU proxy login\n"
            "2. `check_all_for_download_errors()`\n"
            "3. `verify_all_components_are_local()` — may surface new CASRNs; "
            "if so, add to master list and re-run steps 1–3\n"
            "4. `make_full_SciFinder_output_set()` (optional)\n\n"
            "Requires 2 login pauses: OSU proxy + CAS."
        ),
    ),

    # ── Automated Collection ──────────────────────────────────────────────────
    Step(
        id="run-epa1",
        name="EPA 1 — Ingest DTXSID",
        category="AUTO",
        stage="Automated Collection",
        description="Merge CompTox batch results into the master list DTXSIDs.",
        cmd=["python", "master_list_manager.py", "update-dtxsid"],
        dependencies=["fetch-epa1"],
    ),
    Step(
        id="run-epa2",
        name="EPA 2 — EPA Chem Master",
        category="AUTO",
        stage="Automated Collection",
        description="Fetch chemical details from the EPA CompTox API. Incremental and resumable.",
        cmd=["python", "src/01_collection/fetch_epa_chem_data.py"],
        dependencies=["run-epa1"],
    ),
    Step(
        id="run-pubchem",
        name="PubChem GHS",
        category="AUTO",
        stage="Automated Collection",
        description="Fetch GHS hazard data from PubChem for all master-list CASRNs.",
        cmd=["python", "src/01_collection/pub_chem_scraper.py"],
        use_scrape_env=True,
        extra_env={"PYTHONUTF8": "1"},
    ),
    Step(
        id="run-echa2",
        name="ECHA 2 — Harmonised GHS",
        category="AUTO",
        stage="Automated Collection",
        description="Process ECHA Harmonised List into standardised GHS format.",
        cmd=["python", "src/01_collection/ECHA_GHS_scraper.py"],
        dependencies=["fetch-echa1"],
    ),
    Step(
        id="run-atsdr",
        name="ATSDR",
        category="AUTO",
        stage="Automated Collection",
        description="Scrape ATSDR ToxProfiles list.",
        cmd=["python", "src/01_collection/ATSDR_scraper.py"],
        extra_env={"PYTHONUTF8": "1"},
    ),
    Step(
        id="run-coc",
        name="Compounds of Concern",
        category="AUTO",
        stage="Automated Collection",
        description="Scrape EPA Compounds of Concern list.",
        cmd=["python", "src/01_collection/construct_Compounds_of_Concern.py"],
        use_scrape_env=True,
    ),
    Step(
        id="run-nj-rtk",
        name="NJ RTK Datasheets",
        category="AUTO",
        stage="Automated Collection",
        description="Scrape NJ Right to Know hazardous substances.",
        cmd=["python", "src/01_collection/NJ_RTK_data_sheets.py"],
        use_scrape_env=True,
    ),
    Step(
        id="run-niosh",
        name="NIOSH Pocket Guide",
        category="AUTO",
        stage="Automated Collection",
        description="Scrape NIOSH Pocket Guide via Selenium (cdc.gov blocks plain requests).",
        cmd=["python", "src/01_collection/niosh_pocket_guide.py"],
        use_scrape_env=True,
    ),
    Step(
        id="run-cameo",
        name="CAMEO Datasheets",
        category="AUTO",
        stage="Automated Collection",
        description="Scrape CAMEO datasheet links. Slow when new entries exist, but resumable.",
        cmd=["python", "src/01_collection/cameo_data_sheet_links.py"],
        use_scrape_env=True,
    ),
    Step(
        id="run-oecd-chem",
        name="OECD Chemicals",
        category="AUTO",
        stage="Automated Collection",
        description="Scrape the OECD chemicals list.",
        cmd=["python", "src/01_collection/oecd_chemicals.py", "chemicals"],
        use_scrape_env=True,
    ),
    Step(
        id="run-oecd-details",
        name="OECD Chemical Details",
        category="AUTO",
        stage="Automated Collection",
        description="Fetch OECD detail pages for master-list CASRNs. Cached and resumable.",
        cmd=["python", "src/01_collection/oecd_chemicals.py", "details"],
        use_scrape_env=True,
        dependencies=["run-oecd-chem"],
    ),
    Step(
        id="run-oecd-groups",
        name="OECD Groups",
        category="AUTO",
        stage="Automated Collection",
        description="Scrape OECD chemical groups.",
        cmd=["python", "src/01_collection/oecd_chemicals.py", "groups"],
        use_scrape_env=True,
    ),
    Step(
        id="run-gras",
        name="GRAS List",
        category="AUTO",
        stage="Automated Collection",
        description="Download FDA GRAS substances list.",
        cmd=["python", "src/01_collection/GRAS_extract.py"],
        use_scrape_env=True,
    ),
    Step(
        id="run-japan",
        name="Japan NITE GHS — Process",
        category="AUTO",
        stage="Automated Collection",
        description="Translate Japan NITE GHS categories to H-codes.",
        cmd=["python", "src/01_collection/Japan_GHS_Translator.py"],
        dependencies=["fetch-japan"],
    ),
    Step(
        id="run-australia",
        name="Australia Safe Work — Process",
        category="AUTO",
        stage="Automated Collection",
        description="Process Safe Work Australia GHS data into standardised format.",
        cmd=["python", "src/01_collection/extract_australia.py"],
        dependencies=["fetch-australia"],
    ),
    Step(
        id="run-iris",
        name="IRIS — Process",
        category="AUTO",
        stage="Automated Collection",
        description="Extract IRIS chemical list from downloaded Excel file.",
        cmd=["python", "src/01_collection/extract_iris_data.py"],
        dependencies=["fetch-iris"],
    ),
    Step(
        id="run-epa4",
        name="EPA 4 — ChemInfo GHS",
        category="AUTO",
        stage="Automated Collection",
        description="Process ChemInformatics safety files into standardised GHS format.",
        cmd=["python", "src/01_collection/chem_info_safety_scraper.py"],
        dependencies=["fetch-epa3"],
    ),
    Step(
        id="run-epa5",
        name="EPA 5 — ChemInfo Hazard Summary",
        category="AUTO",
        stage="Automated Collection",
        description="Process ChemInformatics hazard files into summary format.",
        cmd=["python", "src/02_processing/cheminfo_processor.py"],
        dependencies=["fetch-epa3"],
    ),

    # ── Integration ───────────────────────────────────────────────────────────
    Step(
        id="run-ghs-consolidator",
        name="GHS Consolidator",
        category="AUTO",
        stage="Integration",
        description="Merge all GHS sources into a single consolidated dataset.",
        cmd=["python", "src/03_integration/GHS_consolidator.py"],
        dependencies=["run-pubchem", "run-echa2", "run-japan", "run-australia", "run-epa4"],
    ),
    Step(
        id="run-hazard-classifier",
        name="Hazard Classifier",
        category="AUTO",
        stage="Integration",
        description="Generate per-chemical GHS hazard classifications across all categories.",
        cmd=["python", "src/03_integration/hazard_classifier.py"],
        dependencies=["run-ghs-consolidator", "run-epa5"],
    ),
    Step(
        id="run-tiered-classifier",
        name="Tiered Classifier",
        category="AUTO",
        stage="Integration",
        description="Generate final tiered hazard classifications.",
        cmd=["python", "src/03_integration/tiered_classifier.py"],
        dependencies=["run-hazard-classifier"],
    ),

    # ── Generation ────────────────────────────────────────────────────────────
    Step(
        id="run-list-of-lists",
        name="List of Lists",
        category="AUTO",
        stage="Generation",
        description="Rebuild list membership data from TSCA, TEDX, Prop65, GRAS, and EPA lists.",
        cmd=["python", "src/04_generation/List_of_lists_section.py"],
        dependencies=["fetch-tsca", "fetch-prop65", "fetch-epa-lists", "run-gras"],
    ),
    Step(
        id="run-build-site",
        name="Build Site",
        category="AUTO",
        stage="Generation",
        description="Generate all chemical markdown pages and tier SVGs.",
        cmd=["python", "src/04_generation/build_site.py"],
        dependencies=["run-tiered-classifier", "run-list-of-lists"],
    ),
    Step(
        id="run-mkdocs",
        name="Generate Site (mkdocs)",
        category="AUTO",
        stage="Generation",
        description="Build the final static site with MkDocs.",
        cmd=["mkdocs", "build"],
        cwd="mkdocs",
        dependencies=["run-build-site"],
    ),
]


def steps_by_id():
    return {s.id: s for s in STEPS}

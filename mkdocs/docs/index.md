---
hide:
  - navigation
---

# Open-FF Chemical Hazard Aggregator

<p class="lead" style="font-size: 1.15rem; opacity: 0.85; line-height: 1.6; margin-bottom: 25px;">
  Making hidden or inaccessible environmental and chemical data visible and usable for researchers, advocates, and the public. This dashboard compiles and simplifies toxicological information from authoritative sources (such as the EPA, ECHA, and international registries) to highlight known risks and expose critical data gaps.
</p>

## Hazard Dashboard

<div class="dashboard-grid">
  <div class="metric-card tier3-card">
    <div class="metric-value">3,216</div>
    <div class="metric-label">Total Materials</div>
    <div class="metric-desc">Chemicals and components tracked in fracking and petrochemical operations.</div>
  </div>
  <div class="metric-card tier1-card">
    <div class="metric-value">1,731</div>
    <div class="metric-label">Tier 1: Known Hazards</div>
    <div class="metric-desc">Chemicals with well-documented, severe hazards officially classified by the GHS.</div>
  </div>
  <div class="metric-card tier2-card">
    <div class="metric-value">854</div>
    <div class="metric-label">Tier 2: Emerging Concerns</div>
    <div class="metric-desc">Substances with significant hazard indicators in literature or regulatory watchlists.</div>
  </div>
  <div class="metric-card tier4-card">
    <div class="metric-value">631</div>
    <div class="metric-label">Tier 4: Data Deficient</div>
    <div class="metric-desc">Materials lacking public testing. Absence of evidence is not evidence of safety.</div>
  </div>
</div>

---

## User Guide

???+ info "Understanding the Tier Summary Graphic"
    Each chemical profile includes a visual graphic that summarizes several hazard classes at a glance.
    
    * <span class="tier-square tier-1"></span> **Tier 1 (Known Hazard)**: Officially classified under the Globally Harmonized System (GHS) as a significant carcinogen, mutagen, reproductive toxin, or high acute toxin.
    * <span class="tier-square tier-2"></span> **Tier 2 (Emerging Hazard)**: Classified as hazardous in scientific literature, predictive models, or advanced watchlists, though GHS classification is pending.
    * <span class="tier-square tier-3"></span> **Tier 3 (Low Hazard)**: Direct toxicological studies demonstrate a favorable safety profile for that hazard class.
    * <span class="tier-square tier-4"></span> **Tier 4 (Data Deficient)**: Insufficient public data exists to draw a scientific conclusion. Treat with precaution.

??? info "How to Use and Filter the Table"
    * **Search & Filter**: Type chemical names or **CASRN** (e.g. `100-41-4`) directly into the search bar at the top of the table.
    * **Find Regulatory Lists**: Filter by regulatory list codes (e.g., search `CWA311HS` for Clean Water Act Hazardous Substances).
    * **Target Specific Tiers**: Filter by specific hazard-class tiers. For example, typing `ENV1` will filter the table to show only chemicals with Tier 1 (Known) Environmental hazards.
    * **Sort**: Click the arrows on column headers to sort numerically or alphabetically.
    * **Export Data**: Use the **Copy** or **CSV** buttons to download your filtered search results.

---

## Interactive Catalog

<div class="table-container">
  <iframe src="./assets/tables/my_table.html" width="100%" height="850px" frameborder="0">
    Your browser does not support iframes.
  </iframe>
</div>




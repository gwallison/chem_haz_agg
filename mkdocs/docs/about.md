# About the Chemical Hazard Aggregator

The **Open-FF Chemical Hazard Aggregator** is a specialized data transparency tool built to centralize, normalize, and simplify complex toxicological information for chemicals used in industrial operations—particularly hydraulic fracturing and petrochemical processing. 

This project is developed by **[Open-FF](https://open-ff.org/)** and sponsored by the **[FracTracker Alliance](https://www.fractracker.org/)**.

---

## Project Mission
Our goal is to make hidden, scattered, or inaccessible environmental and chemical hazard data visible and usable for researchers, advocates, health professionals, and the public. 

Historically, evaluating the safety of complex chemical mixtures required manually searching dozens of disparate national and international registries. This site aggregates these registries into a single, searchable portal, mapping data gaps and highlighting chemicals of high concern.

---

## Hazard vs. Risk
Understanding the distinction between these two concepts is fundamental to using this tool:

*   **Hazard** refers to the *inherent properties* of a substance that make it capable of causing harm. For example, a chemical is hazardous if it is carcinogenic, toxic to aquatic life, or highly corrosive. **Hazard is constant** and does not change based on how the chemical is managed.
*   **Risk** is the *probability* that harm will occur from **exposure** to that hazard (Risk = Hazard × Exposure). 

> [!NOTE]
> **Scope of this Tool**
> This Aggregator catalogs and reports **Hazard**. It does not model exposure pathways, site-specific volumes, or environmental concentrations. Therefore, it does not assess localized **Risk**.

---

## The Four-Tier System
To make complex toxicology studies digestible at a glance, we categorize each chemical into one of four distinct tiers based on the strength of available evidence:

### <span class="tier-square tier-1"></span> Tier 1: Known Hazards
Chemicals with well-documented, severe hazards officially recognized by the **Globally Harmonized System of Classification and Labelling of Chemicals (GHS)**. These represent established, high-certainty dangers such as carcinogenicity, mutagenicity, reproductive toxicity, or extreme acute toxicity.

### <span class="tier-square tier-2"></span> Tier 2: Emerging Concerns & Potential Hazards
Substances that do not yet have a formal GHS "Category 1" designation but show significant evidence of hazard. This tier includes data from peer-reviewed scientific literature, predictive computer models (QSARs), and regulatory watchlists from advanced environmental agencies.

### <span class="tier-square tier-3"></span> Tier 3: Low to Moderate Hazard
Reserved for chemicals that have been robustly studied and demonstrated to have a favorable safety profile. These substances generally do not meet the criteria for Tier 1 or Tier 2.

### <span class="tier-square tier-4"></span> Tier 4: Data Deficient
Assigned to chemicals that lack sufficient public testing or reporting to make a confident safety assessment. 

> [!WARNING]
> **Data Deficient != Safe**
> A Tier 4 designation does not mean a chemical is safe. It means its hazards are **unknown**. In the absence of safety data, we advise a precautionary approach.

---

## Integrated Data Sources
We compile and synthesize data from authoritative environmental and regulatory bodies:

*   **ECHA Chem (European Chemicals Agency)**: Comprehensive substance records, harmonized GHS classifications, and industrial self-classifications.
*   **EPA CompTox Dashboard**: The US Environmental Protection Agency's primary chemical portal, providing DTXSID identifiers and hazard data.
*   **EPA IRIS (Integrated Risk Information System)**: Peer-reviewed assessments focusing on human health effects from environmental exposures.
*   **EPA PPRTV (Provisional Peer-Reviewed Toxicity Values)**: Toxicity values derived for the Superfund program when IRIS values are unavailable.
*   **ATSDR (Agency for Toxic Substances and Disease Registry)**: Public health assessments and toxicological profiles from the US Department of Health and Human Services.
*   **NJ Right-to-Know Hazardous Substances**: Fact sheets detailing worker and community exposure hazards.
*   **CAMEO (Computer-Aided Management of Emergency Operations)**: Safety data sheets developed by NOAA and the EPA for emergency responders.
*   **OECD Reference Pages**: Hazard assessments of high-production volume chemicals.
*   **FDA GRAS (Generally Recognized as Safe)**: Assessments of substances added directly to human food.
*   **EHP Compounds of Concern**: Lists published by the Environmental Health Project.

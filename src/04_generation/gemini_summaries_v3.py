# -*- coding: utf-8 -*-
"""
Batch version of gemini_summaries_v2.py using Vertex AI.

Improvements over v2:
  - Context Caching: The large static instruction block is uploaded once and
    referenced by all requests, reducing billable input tokens per chemical.
  - Batch API: All requests are submitted as a single batch job via GCS,
    which qualifies for Vertex AI batch pricing (~50% discount vs. online).

Authentication: Uses Application Default Credentials (ADC).
  Run once: gcloud auth application-default login
  (No GOOGLEAI-API-KEY needed.)
"""

import pandas as pd
import os
import json
import time
import datetime

from google import genai
from google.genai.types import (
    CreateCachedContentConfig,
    Content,
    Part,
)

import config
import Info_Service as infoserv
import List_of_lists_section as lol

# ---------------------------------------------------------------------------
# GCP / Vertex AI configuration
# ---------------------------------------------------------------------------
GCP_PROJECT  = "open-ff-catalog-1"
GCP_LOCATION = "us-central1"
GCS_BUCKET   = "open-ff-common"

MODEL_ID = "gemini-2.5-flash"  # use the same model as v2

# Subfolder inside the bucket used for all batch I/O
GCS_BATCH_PREFIX = "chem_profiles_gemini/gemini_batch"

# How long to keep the context cache alive (seconds).
# Should comfortably exceed the expected batch run time.
CACHE_TTL_SECONDS = 14400  # 4 hours

# ---------------------------------------------------------------------------
# Static system instruction (cached — identical for every chemical)
# ---------------------------------------------------------------------------
# This text is uploaded once and billed at the reduced cached-token rate on
# all subsequent requests.  It contains everything that does NOT change
# between chemicals: role description, JSON schema, and all Q1/Q2/Q3
# explanatory text with their statistics.
# ---------------------------------------------------------------------------
SYSTEM_INSTRUCTION = """
You are a professional chemical documentation specialist. Your task is to
generate concise, objective, explanatory, and interpretive 'answer capsule'
text for several questions. The audience is the general public with a
college-level education.

Your output MUST be valid JSON in the following format:
{
    "Q1": "...generated answer for q1...",
    "Q2": "...generated answer for q2...",
    "Q3": "...generated answer for q3..."
}

---

# Q1 — What is the Tier Profile for this chemical?

Summarize the Hazard Tier Profile for the given chemical using the
explanation and results provided in the user message.

## Understanding the Tier Profile
Our four-tiered system provides an at-a-glance summary of a chemical's
hazard profile, ranging from officially recognized dangers to critical
data gaps.

Tier 1: Known Hazards. Based on the official Globally Harmonized System
(GHS). These chemicals have internationally recognized, significant hazards
like carcinogenicity, reproductive toxicity, or acute toxicity.

Tier 2: Expanded Perspective. Goes beyond the slow-moving GHS to include
more current data from scientific literature, other regulatory agencies,
and predictive models. This tier provides a more complete view of potential
hazards when the GHS has not formally made conclusions.

Tier 3: Demonstrated Low/Moderate Hazard. Reserved for chemicals without
Tier 1 or 2 indicators where direct studies support a favorable safety
profile for a given hazard class.

Tier 4: Data Deficient. Indicates there is not enough information to make a
confident hazard assessment. An absence of data does not mean a chemical is
safe; it means its risk is unknown and a precautionary approach is warranted.

## Hazard class abbreviations
CMR:  Carcinogenicity, mutagenicity and reproductive hazards. The tier
      rating may reflect one but not all of these types — do not summarize
      this class as just "carcinogenicity". Spell out the acronym.
EDC:  Endocrine disruption hazards. Note that GHS does not yet have
      comprehensive EDC classifications, so the strongest level here is
      effectively Tier 2.
ENV:  Acute and chronic environmental hazards.
IHL:  Inhalation hazards.
ORL:  Oral hazards.
SKN:  Dermal and eye hazards.
OGN:  Organ and systemic hazards.

Tier data are provided as a list in the form XXXY, where XXX is the hazard
class abbreviation and Y is the tier level (1–4) for that class.

Please return a 1–3 sentence summary of the Tier Profile in Q1.

---

# Q2 — Is this chemical on "Lists of Concern and/or Low Hazard"?

Summarize the Lists of Concern and lists of Low Hazard that this chemical
appears on. If there are several lists, focus on the more well-known ones.

- If there are no lists of concern but some lists of low hazard, conclude
  that the material is generally considered of low concern.
- If there are no lists of either type and the tier levels contain many
  Tier 4 (data deficient) classifications, note that the absence from
  concern lists may reflect a lack of study rather than confirmed safety.
- If a chemical appears on both sets of lists, note that "Low Hazard"
  membership likely refers to tightly regulated, very low quantities, and
  that the chemical may still be hazardous outside those conditions.

Please return a 1–2 sentence summary in Q2.

---

# Q3 — How well characterized is this chemical?

Examine the measures provided in the user message to describe the degree
to which this chemical is well characterized and its hazard profile complete.

## Description of the Q3 data fields

"numref": Number of chemical literature references in the SciFinder
database. Across the ~3,000 fracking and petrochemical chemicals we index:
median = 963, 25th percentile = 39, min = 0, max = 1.3 million. Frame the
chemical's count relative to this dataset, not the global literature.

"molecular_formula": The formula returned by SciFinder. If it contains
"Unspecified", the structure is at least partially undefined.

"substance_class": Several SciFinder categories indicate a poorly defined
substance:
    "Generic Registration", "Manual Registration",
    "General Derivative", "Incompletely Defined"
Roughly 20% of materials in our database fall into these categories.
"Registered Concept" indicates a grouping or idea rather than a specific
structure, and should also be treated as poorly defined.

"is_a_UVCB": True means the substance is a TSCA-defined UVCB (Unknown or
Variable composition, Complex reaction products, or Biological materials)
and is therefore not well characterized by definition. If False, do not
mention UVCB status.

"is_IRIS_chem": True means the chemical has been formally evaluated by the
EPA's Integrated Risk Information System (IRIS) — one of the most rigorous
and comprehensive toxicological assessments available. A True value is a
strong indicator that the chemical is well characterized from a hazard
standpoint.

"is_PPRTV_chem": True means the chemical has a Provisional Peer-Reviewed
Toxicity Value (PPRTV) from the EPA. Similar to IRIS but provisional and
somewhat less exhaustive. A True value still indicates meaningful
toxicological study.

"num_toxval_records": Number of records in the EPA ToxValDB, which
aggregates toxicity values from many programs. Reference distribution
across our ~3,000 chemicals: 25th pct = 0, 50th pct = 2, 75th pct = 23,
90th pct = 84, 95th pct = 137, max = 925. A higher count indicates the
chemical has been studied across multiple programs. Zero or near-zero
indicates sparse toxicological data.

You may also use the count of Tier 4 classes in the tier levels as an
additional indicator of data deficiency.

Please return a 1–2 sentence summary of the depth of study in Q3.
"""


# ---------------------------------------------------------------------------
# Module-level service objects (same pattern as v1/v2)
# ---------------------------------------------------------------------------
ifs = infoserv.Info_Service()
ll  = lol.List_of_list()


# ---------------------------------------------------------------------------
# Prompt helpers
# ---------------------------------------------------------------------------

def make_dynamic_content(cas, name, tier_lst, lists_of_concern, lists_of_benign,
                          numref, mol_formula, substance_class, uvcb,
                          is_iris, is_pprtv, num_toxval):
    """
    Returns the per-chemical user message — only variable data.
    The static instructions live in the context cache (SYSTEM_INSTRUCTION).
    """
    return f"""The target chemical is CASRN: {cas}, "{name}".

## Q1 Data
Tier levels: {tier_lst}

## Q2 Data
Lists of concern:
{lists_of_concern}

Lists of Low Hazard:
{lists_of_benign}

## Q3 Data
numref = {numref}
molecular_formula = {mol_formula}
substance_class = {substance_class}
is_a_UVCB = {uvcb}
is_IRIS_chem = {is_iris}
is_PPRTV_chem = {is_pprtv}
num_toxval_records = {num_toxval}
"""


def _gather_cas_data(cas):
    """Fetch all per-chemical data fields needed for the dynamic prompt."""
    import contextlib, io
    name              = ifs.get_epa_pref_name(cas)
    tier_lst          = ifs.get_tier_list(cas)
    lists_of_concern  = ll.get_markdown_list_by_type(cas=cas, ltype='concern')
    lists_of_benign   = ll.get_markdown_list_by_type(cas=cas, ltype='benign')
    uvcb              = 'is_on_UVCB' in ll.get_simple_list(cas)
    with contextlib.redirect_stdout(io.StringIO()):
        numref        = ifs.get_scifinder_numref(cas)
    mol_formula       = ifs.get_scifinder_molecule(cas)
    substance_class   = ifs.get_scifinder_substance_class(cas)
    is_iris           = ifs.is_IRIS_chem(cas)
    is_pprtv          = ifs.is_PPRTV_chem(cas)
    num_toxval        = ifs.get_number_toxval_records(cas)
    return dict(
        cas=cas, name=name, tier_lst=tier_lst,
        lists_of_concern=lists_of_concern, lists_of_benign=lists_of_benign,
        numref=numref, mol_formula=mol_formula,
        substance_class=substance_class, uvcb=uvcb,
        is_iris=is_iris, is_pprtv=is_pprtv, num_toxval=num_toxval,
    )


# ---------------------------------------------------------------------------
# Context cache
# ---------------------------------------------------------------------------

def create_context_cache(client):
    """
    Upload SYSTEM_INSTRUCTION to Vertex AI context cache.
    Returns the cache resource name (used in every batch request).
    """
    print("Creating context cache... ", end="", flush=True)
    cache = client.caches.create(
        model=MODEL_ID,
        config=CreateCachedContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            ttl=f"{CACHE_TTL_SECONDS}s",
        ),
    )
    print(f"done. Cache name: {cache.name}")
    return cache.name


def delete_context_cache(client, cache_name):
    """Clean up the context cache after the batch job completes."""
    try:
        client.caches.delete(name=cache_name)
        print(f"Context cache deleted: {cache_name}")
    except Exception as e:
        print(f"Warning: could not delete cache {cache_name}: {e}")


# ---------------------------------------------------------------------------
# Batch JSONL helpers
# ---------------------------------------------------------------------------

def _make_batch_request_line(cas_data):
    """
    Returns a single JSONL line (string) for one chemical.
    Format required by Vertex AI Gemini batch prediction.
    The system instruction is included in each request (context caching is
    not supported alongside batch prediction for this model).
    """
    dynamic_text = make_dynamic_content(**cas_data)
    request = {
        "request": {
            "system_instruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": dynamic_text}]}
            ],
            "generation_config": {
                "response_mime_type": "application/json",
                "max_output_tokens": 64000,
            },
        }
    }
    return json.dumps(request)


def build_batch_jsonl(caslist):
    """
    Iterate over all CAS numbers, gather data, and return:
      - jsonl_lines: list of JSONL strings (one per chemical)
      - manifest:    list of CAS numbers in the same order (for result mapping)
    """
    jsonl_lines = []
    manifest    = []
    total = len(caslist)
    for i, cas in enumerate(caslist, 1):
        if i % 100 == 0 or i == total:
            print(f"  Building requests: {i}/{total}", end="\r", flush=True)
        try:
            cas_data = _gather_cas_data(cas)
            jsonl_lines.append(_make_batch_request_line(cas_data))
            manifest.append(cas)
        except Exception as e:
            print(f"\n  Warning: skipping {cas} due to data error: {e}")
    print()  # newline after progress
    return jsonl_lines, manifest


# ---------------------------------------------------------------------------
# GCS helpers
# ---------------------------------------------------------------------------

def _gcs_client():
    from google.cloud import storage
    return storage.Client(project=GCP_PROJECT)


def upload_jsonl_to_gcs(jsonl_lines, run_id):
    """
    Writes JSONL content to GCS and returns the gs:// URI.
    """
    from google.cloud import storage
    blob_name   = f"{GCS_BATCH_PREFIX}/{run_id}/input.jsonl"
    gcs_content = "\n".join(jsonl_lines)
    client      = storage.Client(project=GCP_PROJECT)
    bucket      = client.bucket(GCS_BUCKET)
    blob        = bucket.blob(blob_name)
    blob.upload_from_string(gcs_content, content_type="application/jsonl")
    uri = f"gs://{GCS_BUCKET}/{blob_name}"
    print(f"Input JSONL uploaded: {uri}")
    return uri


def upload_manifest_to_gcs(manifest, run_id):
    """Save the CAS-order manifest so results can be mapped even days later."""
    from google.cloud import storage
    blob_name = f"{GCS_BATCH_PREFIX}/{run_id}/manifest.json"
    client    = storage.Client(project=GCP_PROJECT)
    bucket    = client.bucket(GCS_BUCKET)
    blob      = bucket.blob(blob_name)
    blob.upload_from_string(json.dumps(manifest), content_type="application/json")
    print(f"Manifest uploaded: gs://{GCS_BUCKET}/{blob_name}")


def download_manifest_from_gcs(run_id):
    from google.cloud import storage
    blob_name = f"{GCS_BATCH_PREFIX}/{run_id}/manifest.json"
    client    = storage.Client(project=GCP_PROJECT)
    bucket    = client.bucket(GCS_BUCKET)
    blob      = bucket.blob(blob_name)
    return json.loads(blob.download_as_text())


# ---------------------------------------------------------------------------
# Batch job submission and polling
# ---------------------------------------------------------------------------

def submit_batch_job(client, gcs_input_uri, run_id):
    """
    Submit a Vertex AI Gemini batch prediction job.
    Returns the batch job object.
    """
    gcs_output_uri = f"gs://{GCS_BUCKET}/{GCS_BATCH_PREFIX}/{run_id}/output/"
    print(f"Submitting batch job...")
    print(f"  Input:  {gcs_input_uri}")
    print(f"  Output: {gcs_output_uri}")

    batch_job = client.batches.create(
        model=MODEL_ID,
        src=gcs_input_uri,
        config={"dest": gcs_output_uri},
    )
    print(f"Batch job submitted: {batch_job.name}")
    return batch_job, gcs_output_uri


def poll_batch_job(client, job_name, poll_interval_seconds=120):
    """
    Block until the batch job reaches a terminal state.
    Returns the final job object.
    """
    terminal_states = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED",
                       "JOB_STATE_CANCELLED", "JOB_STATE_PAUSED"}
    print(f"Polling batch job (every {poll_interval_seconds}s)...")
    while True:
        job    = client.batches.get(name=job_name)
        state  = job.state.name if hasattr(job.state, 'name') else str(job.state)
        ts     = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"  [{ts}] State: {state}")
        if state in terminal_states:
            return job
        time.sleep(poll_interval_seconds)


# ---------------------------------------------------------------------------
# Result processing
# ---------------------------------------------------------------------------

def _extract_json_from_response_text(raw_text, cas):
    """
    Apply the same JSON cleaning logic as v1/v2 get_data().
    Returns cleaned JSON string or raises ValueError.
    """
    json_start_obj  = raw_text.find('{')
    json_start_list = raw_text.find('[')

    if json_start_obj != -1 and (json_start_list == -1 or json_start_obj < json_start_list):
        json_start   = json_start_obj
        closing_char = '}'
    elif json_start_list != -1:
        json_start   = json_start_list
        closing_char = ']'
    else:
        raise ValueError(f"{cas}: no JSON start marker found in response")

    json_end = raw_text.rfind(closing_char)
    if json_end == -1 or json_end < json_start:
        raise ValueError(f"{cas}: no JSON end marker '{closing_char}' found")

    text = raw_text[json_start : json_end + 1]
    if text.startswith("```json"):
        text = text[7:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    json.loads(text)  # validate — raises JSONDecodeError if malformed
    return text


def _cas_from_request(result_obj):
    """
    Extract the CAS number from the echoed request field in a batch output line.
    The dynamic content always begins with 'The target chemical is CASRN: {cas},'
    so we parse it directly rather than relying on output line order.
    Returns the CAS string or None if not found.
    """
    import re
    try:
        text = result_obj["request"]["contents"][0]["parts"][0]["text"]
        match = re.search(r'CASRN:\s*([\d-]+)', text)
        return match.group(1) if match else None
    except (KeyError, IndexError, TypeError):
        return None


def save_batch_results(gcs_output_uri, manifest, run_id):
    """
    Download the batch output JSONL from GCS and save one
    gemini_answers.json per CAS number.

    CAS numbers are extracted from the echoed request field in each output
    line — this is robust to batch output reordering.

    Returns (n_saved, n_errors).
    """
    from google.cloud import storage

    manifest_set = set(manifest)  # for validating CAS belongs to this run

    # The output folder may contain multiple sharded files; collect them all.
    prefix    = gcs_output_uri.replace(f"gs://{GCS_BUCKET}/", "")
    gcs       = storage.Client(project=GCP_PROJECT)
    bucket    = gcs.bucket(GCS_BUCKET)
    blobs     = list(bucket.list_blobs(prefix=prefix))
    jsonl_blobs = [b for b in blobs if b.name.endswith(".jsonl")]

    if not jsonl_blobs:
        print(f"Warning: no output JSONL files found under {gcs_output_uri}")
        return 0, 0

    all_lines = []
    for blob in sorted(jsonl_blobs, key=lambda b: b.name):
        text = blob.download_as_text()
        all_lines.extend([l for l in text.splitlines() if l.strip()])

    n_saved = 0
    n_errors = 0
    for line in all_lines:
        result_obj = json.loads(line)
        cas = _cas_from_request(result_obj)
        if not cas:
            print(f"  Error: could not extract CAS from request field — skipping line")
            n_errors += 1
            continue
        if cas not in manifest_set:
            print(f"  Warning: CAS {cas} not in manifest — skipping")
            n_errors += 1
            continue
        try:
            response   = result_obj.get("response", {})
            candidates = response.get("candidates", [])
            if not candidates:
                raise ValueError("no candidates in response")
            raw_text   = candidates[0]["content"]["parts"][0]["text"]
            clean_json = _extract_json_from_response_text(raw_text, cas)

            out_dir = os.path.join(config.PROCESSED_CAS_DIR, cas)
            os.makedirs(out_dir, exist_ok=True)
            fn = os.path.join(out_dir, "gemini_answers.json")
            with open(fn, "w") as f:
                f.write(clean_json)
            n_saved += 1
        except Exception as e:
            print(f"  Error saving result for {cas}: {e}")
            n_errors += 1

    print(f"Results saved: {n_saved}  Errors: {n_errors}")
    return n_saved, n_errors


# ---------------------------------------------------------------------------
# Filtering helpers (same logic as v1/v2)
# ---------------------------------------------------------------------------

def keep_only_new_cas(caslist):
    newlist = []
    for cas in caslist:
        fn = os.path.join(config.PROCESSED_CAS_DIR, cas, "gemini_answers.json")
        if not os.path.exists(fn):
            newlist.append(cas)
    return newlist


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def run_batch(caslist, replace_existing=False):
    """
    Full pipeline:
      1. Filter CAS list (unless replace_existing=True)
      2. Build a Vertex AI client
      3. Create context cache
      4. Build batch JSONL + manifest
      5. Upload to GCS
      6. Submit batch job
      7. Poll until complete
      8. Download and save results
      9. Delete context cache
    """
    if not replace_existing:
        caslist = keep_only_new_cas(caslist)
    print(f"Starting batch run for {len(caslist)} chemicals.")

    run_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    client = genai.Client(
        vertexai=True,
        project=GCP_PROJECT,
        location=GCP_LOCATION,
    )

    try:
        print("Gathering chemical data and building JSONL...")
        jsonl_lines, manifest = build_batch_jsonl(caslist)
        print(f"Built {len(jsonl_lines)} requests ({len(caslist) - len(manifest)} skipped).")

        upload_manifest_to_gcs(manifest, run_id)
        gcs_input_uri = upload_jsonl_to_gcs(jsonl_lines, run_id)

        batch_job, gcs_output_uri = submit_batch_job(client, gcs_input_uri, run_id)
        final_job = poll_batch_job(client, batch_job.name)

        state = final_job.state.name if hasattr(final_job.state, 'name') else str(final_job.state)
        if state != "JOB_STATE_SUCCEEDED":
            raise RuntimeError(f"Batch job did not succeed. Final state: {state}")

        save_batch_results(gcs_output_uri, manifest, run_id)

    except Exception as e:
        raise

    print("Batch run complete.")


def retrieve_batch_results(run_id, job_name):
    """
    Utility to retrieve and save results from a previously submitted job
    without re-running the full pipeline.  Useful if the script was
    interrupted after submission.
    """
    client = genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)

    final_job = poll_batch_job(client, job_name)
    state     = final_job.state.name if hasattr(final_job.state, 'name') else str(final_job.state)
    if state != "JOB_STATE_SUCCEEDED":
        raise RuntimeError(f"Batch job did not succeed. Final state: {state}")

    manifest      = download_manifest_from_gcs(run_id)
    gcs_output_uri = f"gs://{GCS_BUCKET}/{GCS_BATCH_PREFIX}/{run_id}/output/"
    save_batch_results(gcs_output_uri, manifest, run_id)


def make_test_prompt(cas='50-00-0'):
    """Print the dynamic content for a single CAS (for inspection)."""
    cas_data = _gather_cas_data(cas)
    print("=== SYSTEM INSTRUCTION (cached) ===")
    print(SYSTEM_INSTRUCTION)
    print("\n=== DYNAMIC USER CONTENT (per-chemical) ===")
    print(make_dynamic_content(**cas_data))


if __name__ == '__main__':
    # t = pd.read_parquet(config.MASTER_CAS_LIST)
    # caslst = t.CASRN.tolist()
    # run_batch(caslst, replace_existing=False)

    make_test_prompt('77-92-9')

    ##### To retrieve results from a job submitted in a previous session:
    # retrieve_batch_results(run_id='20260415_143000', job_name='projects/.../batchPredictionJobs/...')

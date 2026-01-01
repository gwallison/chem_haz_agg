# -*- coding: utf-8 -*-
"""
Used to build short text summaries of hazard analysis and compilations

"""
import pandas as pd
import numpy as np
import os
import json # Import json for validation

from google import genai # Use the new package
from google.genai.types import GenerateContentConfig, HttpOptions # Import the correct classes

# from IPython.display import HTML, display
# from IPython.display import Markdown as md


import config
import Info_Service as infoserv
import List_of_lists_section as lol
# import chem_profiles.config as config

cas = '50-00-0'
cas = '68424-85-1'
ifs = infoserv.Info_Service()
ifs.get_tier_list(cas=cas)
ll = lol.List_of_list()
lists_of_concern = ll.get_markdown_list_by_type(cas=cas,
                                                 ltype='concern')
ex_format = """
        {
            "Q1":"...generated answer for q1...",
            "Q2":"...generated answer for q2...",
            "Q3":"...generated answer for q3...",
            
        }
"""

def make_prompt(cas,name,tier_lst,lists_of_concern,ifs,uvcb):
    prompt = f"""
    You are a professional chemical documentation specialist. Your task is to generate concise, objective, explanatory, and interpretive 'answer capsule' text to a several questions.  The audience is the general public with a college-level education.
    Your output will be in JSON format, organized by the different questions and their number.
    Example JSON format:
        {ex_format}
        
    The target chemical is CASRN: {cas}, "{name}".
    
    # Question: What is the Tier Profile for this chemical?
    Question Number: Q1
    Task: Summarize the Hazard Tier Profile for the given chemical by using the explanation and results below.
    
    ## Understanding the Tier Profile
    Our four-tiered system provides an at-a-glance summary of a chemical's hazard profile, ranging from officially recognized dangers to critical data gaps.
    Tier 1: Known Hazards Based on the official Globally Harmonized System (GHS). These chemicals have internationally recognized, significant hazards like carcinogenicity, reproductive toxicity, or acute toxicity.
    Tier 2: Expanded Perspective Goes beyond the slow-moving GHS to include more current data from scientific literature, other regulatory agencies, and predictive models. This tier provides a more complete view of potential hazards when the GHS has not formally made conclusions.
    Tier 3: Demonstrated Low/Moderate Hazard This is reserved for chemicals without Tier 1 or 2 indicators, but direct studies support a favorable safety profile for a given hazard class.
    Tier 4: Data Deficient Indicates there is not enough information to make a confident hazard assessment. An absence of data does not mean a chemical is safe; it means its risk is unknown and a precautionary approach is warranted.
    ### Hazard class levels
    Tier rating are developed for several classes of hazards (each give a three letter abbreviation):
    CMR:	Carcinogenicity, mutagenicity and reproductive hazards - it is important to note that the tier rating may be from a hazard value from one but not all of these individual types.  Therefore do not summarize this class as just "carcinogeneity" for example. You may want to spell out the acronym. 
    EDC:	Endocrine disruption hazards (note that GHS does not yet have comprehensive classification of EDCs. Therefore, the strongest hazard level in this system is effectively level 2)
    ENV: 	Acute and chronic environmental hazards
    IHL:	Inhalation hazards
    ORL:	Oral hazards
    SKN:	Dermal and eye hazards
    OGN:	Organ and systemic hazards
    
    These tier data are passed to you as a list in the form of XXXY, where XXX is the hazard class abreviation and Y is the tier level for that class.
    
    The tier levels are {tier_lst}
    
    Please return your 1-3 sentence summary of the Tier Profile in the JSON output.
    
    
    # Question: Is this chemical on "Lists of Concern"?
    Question Number: Q2
    Task: Summarize the Lists of Concern that this chemical is on.  If there are several lists,
    you may focus on just a few of the more well known lists.  If there are no lists of concern and the tier level classifications
    have many level '4' (data deficient), point out that the lack of lists of concern
    may be due to the due to the lack of study of the material.
    
    The lists of concern for this chemical are:
    {lists_of_concern}.
    
    Please return your 1-2 sentence summary of the Tier Profile in the JSON output.
    
    
    # Question: How well characterized is this chemical?
    QuestionNumber: Q3
    Task: Examine the measures below to describe the degree to which this chemical is well characterized,
    and therefore it's hazard profile is complete.
    ## Description of the data below:

        "numref" is the number of literature references in the SciFinder database. Across the set of chemicals
        we characterize, the median numref is 963 references, the 25 percentile is 39 references, the minimum is zero references and the maximum 
        is 1.3 million references.

        "molecular_formula" is the molecular formula returned by SciFinder.  If it has
        the term "Unspecified" in it, that the material's formula is at least partially undefined.
        
        "substance_class": Several categories in the SciFinder Substance Class indicate that the material is poorly defined. These are: 
            "Generic Registration",
            "Manual Registration",
            "General Derivative",
            "Incompletely Defined", and
            "Registered Concept"
            Roughly 20% of materials in our database are so defined.
        
        "is_a_UVCB" indicates that the material is a TSCA defined "UVCB" and therefore not well characterized.
        
    You may also use the number of Tier 4 classes in the tier levels as a measure of data deficiency.
    
    ## Data for Q3
    numref = {ifs.get_scifinder_numref(cas)}
    molecular_formula = {ifs.get_scifinder_molecule(cas)}
    substance_class = {ifs.get_scifinder_substance_class(cas)}
    is_a_UVCB = {uvcb}

    Please return your 1-2 sentence summary of the depth of study of this chemical in the JSON output.

    """
    return prompt

def get_data( prompt):
    api_key = os.environ.get("GOOGLEAI-API-KEY") # Standard env var name, adjust if needed
    if not api_key:
        raise ValueError("GOOGLEAI-API-KEY environment variable not set.")

    # 1. Create the client and set the timeout
    client = genai.Client(
        api_key=api_key,
        http_options=HttpOptions(timeout=600_000) # 600 seconds = 600,000 milliseconds
    )

    # # print(f"Uploading file: {fn}...")
    # # 2. Use the client to upload the file (note: 'file=fn')
    # myfile = client.files.upload(file=fn)
    # # print(f"File uploaded: {myfile.name}")

    model_id = "gemini-2.5-flash" # seems to do the work, for cheaper
    # model_id = "gemini-2.5-pro" # 4x more expensive
    # model_id = "gemini-3-pro-preview"

    # (No need to create 'model' object anymore)

    # 3. Use the correct 'GenerateContentConfig' class
    config = GenerateContentConfig(
        max_output_tokens=64000,
        # temperature=0.2 # Optional: Lower temperature for more deterministic JSON output
        response_mime_type="application/json" # Request JSON directly!
    )

    # print(f"Generating content using model {model_id}...")
    try:
        # 4. Call 'generate_content' from the client
        response = client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=config
        )
    
        # --- String Cleaning Logic ---
        raw_text = response.text # Get the raw text first
        
        # 1. Look for the start of the JSON structure (either list or object)
        json_start_index_obj = raw_text.find('{')
        json_start_index_list = raw_text.find('[')
        
        # Determine the actual start and the expected closing character
        if json_start_index_obj != -1 and (json_start_index_list == -1 or json_start_index_obj < json_start_index_list):
            # JSON starts with an object '{'
            json_start_index = json_start_index_obj
            closing_char = '}'
        elif json_start_index_list != -1:
            # JSON starts with a list '[' (or list is before object, if both exist)
            json_start_index = json_start_index_list
            closing_char = ']'
        else:
            # Could not find the expected JSON structure
            print("Error: Could not find valid JSON start '{' or '[' markers in the response.")
            # ... (keep your existing error and feedback printing)
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback: print(f"Prompt Feedback: {response.prompt_feedback}")
            if hasattr(response.candidates[0], 'safety_ratings') and response.candidates[0].safety_ratings: print(f"Safety Ratings: {response.candidates[0].safety_ratings}")
            raise ValueError("Failed to extract JSON structure from API response.")
    
    
        # 2. Find the end of the JSON structure (search for the closing character from the end)
        json_end_index = raw_text.rfind(closing_char)
    
        if json_end_index == -1 or json_end_index < json_start_index:
            print(f"Error: Could not find the expected JSON end marker '{closing_char}' in the response.")
            raise ValueError("Failed to extract JSON structure from API response.")
        
        # 3. Extract the substring
        # +1 on end_index because slicing is exclusive of the end position
        response_text = raw_text[json_start_index : json_end_index + 1]
        
        # 4. Remove any wrapping Markdown fence if present (keep existing logic)
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
     
        # --- JSON Validation ---
        try:
            # Attempt to parse the JSON to ensure it's valid
            json.loads(response_text)
            # print("JSON successfully parsed.")
            return response_text
        except json.JSONDecodeError as e:
            print(f"Error: Generated text is not valid JSON. Error: {e}")
            print("--- Truncated or Invalid Response ---")
            print(response_text)
            print("------------------------------------")
            # Optionally, you could check response.prompt_feedback for block reasons
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                 print(f"Prompt Feedback: {response.prompt_feedback}")
            if hasattr(response, 'candidates') and response.candidates[0].finish_reason:
                 print(f"Finish Reason: {response.candidates[0].finish_reason}")
                 if response.candidates[0].finish_reason.name == 'MAX_TOKENS':
                     print(">>> Suggestion: The output was likely truncated due to max_output_tokens limit.")
                 elif response.candidates[0].finish_reason.name != 'STOP':
                      print(">>> Suggestion: Output may have been stopped for safety or other reasons.")
    
            raise ValueError("Failed to get valid JSON from API. Output might be truncated or invalid.") from e

    except Exception as e:
        print(f"An error occurred during API call: {e}")
        # 5. Use the client to delete the file
        # print(f"Deleting uploaded file: {myfile.name}")
        # client.files.delete(name=myfile.name)
        raise # Re-raise the exception after cleanup

    # finally:
        # --- File Cleanup ---
        # It's important to delete the file from Google's storage
        # once you are done with it to avoid accumulating files.
        # print(f"Deleting uploaded file: {myfile.name}")
        # 6. Use the client to delete the file here too
        # client.files.delete(name=myfile.name)

def keep_only_new_cas(caslist):
    newlist = []
    for cas in caslist:
        fn = os.path.join(config.PROCESSED_CAS_DIR,cas,'gemini_answers.json')
        if not os.path.exists(fn):
            newlist.append(cas)
    return newlist


def make_set(caslist,replace_existing=False):
    if not replace_existing:
        caslist = keep_only_new_cas(caslist)
    print(f'Starting run of {len(caslist)}')
    for cas in caslist:
        print(f'{cas}... ',end='')
        name = ifs.get_epa_pref_name(cas)
        # print(name)
        tier_lst = ifs.get_tier_list(cas)
        ll = lol.List_of_list()
        lists_of_concern = ll.get_markdown_list_by_type(cas=cas,
                                                        ltype='concern')
        uvcb = 'is_on_UVCB' in ll.get_simple_list(cas)
        
        prompt = make_prompt(cas,name,tier_lst,lists_of_concern,ifs,uvcb)
        # print(prompt)
        res = get_data(prompt)
        os.makedirs(os.path.join(config.PROCESSED_CAS_DIR,cas),
                 exist_ok=True)
        fn = os.path.join(config.PROCESSED_CAS_DIR,cas,'gemini_answers.json')
        with open(fn,'w') as f:
            f.write(res)
            

            
if __name__ == '__main__':
    t = pd.read_parquet(config.MASTER_CAS_LIST)
    caslst = t.CASRN.tolist()
    make_set(caslst, replace_existing=False)    
    
     

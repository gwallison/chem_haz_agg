import os
import requests
import json
import argparse

# A list of potential base URLs for the API.
# The script will try them in order until one succeeds.
API_HOSTS = [
    "https://comptox.epa.gov/ctx-api"  # <-- FIXED: This is now a valid string
]

def _make_request(method: str, endpoint: str, stream: bool = False, **kwargs):
    """
    A robust helper function to make requests to the EPA API.
    It iterates through known API hosts and handles common errors.

    Args:
        method: The HTTP method (e.g., 'GET', 'POST').
        endpoint: The API endpoint path.
        stream: If True, returns the raw response object for streaming.
        **kwargs: Additional arguments to pass to requests.request.

    Returns:
        The JSON response as a Python object, the raw response object if
        streaming, or None on error.
    """
    last_error = None
    kwargs.setdefault('timeout', 180) # Increased timeout for potentially large requests

    for base_url in API_HOSTS:
        url = f"{base_url}{endpoint}"
        try:
            # print(f"Attempting {method} request to {url} with a {kwargs['timeout']} second timeout...")
            response = requests.request(method, url, stream=stream, **kwargs)
            # print(f"Request to {url} completed with status code: {response.status_code}")
            response.raise_for_status()

            if stream:
                # print("Streaming mode enabled. Returning raw response object.")
                return response

            # print("Parsing JSON response...")
            json_response = response.json()
            # print("JSON parsing complete.")
            return json_response
            
        except requests.exceptions.Timeout:
            print(f"Request to {url} timed out.")
            last_error = "Timeout"
            continue
        except requests.exceptions.ConnectionError as conn_err:
            print(f"Connection to {base_url} failed: {conn_err}")
            last_error = conn_err
            continue
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred with {url}: {http_err}")
            print(f"Status Code: {http_err.response.status_code}")
            print(f"Response Text: {http_err.response.text}")
            return None
        except json.JSONDecodeError as json_err:
            print(f"Failed to parse JSON response from {url}: {json_err}")
            print("The server may have returned an incomplete or invalid response.")
            last_error = json_err
            break
        except requests.exceptions.RequestException as err:
            print(f"An unexpected error occurred with {url}: {err}")
            last_error = err
            break
    
    print(f"All API hosts failed. Last error: {last_error}")
    return None


def get_chemical_details(dtxsid: str = 'DTXSID7020182'):
    """
    Fetches chemical details from the EPA CompTox API for a given DTXSID.
    """
    api_key = os.environ.get("EPA_API_KEY")
    if not api_key:
        print("Error: EPA_API_KEY environment variable not set.")
        return None
    endpoint = f"/chemical/detail/search/by-dtxsid/{dtxsid}"
    headers = {'accept': 'application/json', 'x-api-key': api_key}
    print(f"\nQuerying API for DTXSID: {dtxsid}...")
    return _make_request('GET', endpoint, headers=headers)


# def get_dtxsid_by_casrn(casrn: str):
#     """
#     Fetches chemical details from the EPA CompTox API for a given CASRN.
#     This uses the /chemical/detail/search/by-casrn endpoint,
#     mirroring the known-working dtxsid endpoint.
#     """
#     api_key = os.environ.get("EPA_API_KEY")
#     if not api_key:
#         print("Error: EPA_API_KEY environment variable not set.")
#         return None
    
#     # <-- UPDATED to new hypothesis
#     endpoint = f"/chemical/detail/search/by-casrn/{casrn}"
    
#     headers = {'accept': 'application/json', 'x-api-key': api_key}
#     # Keep this query quiet to avoid flooding the console
#     # print(f"\nQuerying API for CASRN: {casrn}...")
#     return _make_request('GET', endpoint, headers=headers)


# def get_dtxsids_by_casrns(casrns: list[str]):
#     """
#     Finds DTXSIDs for a given list of CASRN numbers
#     using the new /chemical/search/list batch endpoint.
#     (NOTE: THIS ENDPOINT IS NOT WORKING, DO NOT USE)
#     """
#     api_key = os.environ.get("EPA_API_KEY")
#     if not api_key:
#         print("Error: EPA_API_KEY environment variable not set.")
#         return None
        
#     # <-- This is the endpoint that keeps failing with 404
#     endpoint = "/chemical/search/list"
    
#     headers = {
#         'accept': 'application/json',
#         'Content-Type': 'application/json',
#         'x-api-key': api_key
#     }
    
#     # <-- This is the new, correct payload structure for this endpoint
#     payload = {"identifiers": casrns, "searchBy": "CASRN"}
    
#     # Only show the first 3 CASRNs to keep the log clean
#     casrn_preview = ', '.join(casrns[:3])
#     if len(casrns) > 3:
#         casrn_preview += ", ..."
#     print(f"Querying new batch endpoint for {len(casrns)} CASRNs: {casrn_preview}")
    
#     return _make_request('POST', endpoint, headers=headers, data=json.dumps(payload))


def get_all_chemicals_count():
    """
    Counts all chemicals by requesting a projection of only their IDs.
    This is much more memory-efficient than downloading all details.
    """
    api_key = os.environ.get("EPA_API_KEY")
    if not api_key:
        print("Error: EPA_API_KEY environment variable not set.")
        return None
    endpoint = "/chemical/all"
    headers = {'accept': 'application/json', 'x-api-key': api_key}
    params = {'projection': 'all-ids'}

    print("Querying API for all chemical IDs...")
    response_data = _make_request('GET', endpoint, headers=headers, params=params)

    if isinstance(response_data, list):
        return len(response_data)
    
    print("Failed to retrieve a list of IDs from the API.")
    if response_data is not None:
        print("\n--- Raw API Response ---")
        print(json.dumps(response_data, indent=2))
        
    return None


# def create_casrn_dtxsid_map():
#     """
#     Builds a dictionary mapping CASRNs to a list of DTXSIDs by fetching
#     all chemicals from the API using pagination. This handles one-to-many
#     relationships between CASRNs and DTXSIDs.
    
#     Returns:
#         A dictionary where keys are CASRNs and values are lists of DTXSIDs,
#         or None on error.
#     """
#     api_key = os.environ.get("EPA_API_KEY")
#     if not api_key:
#         print("Error: EPA_API_KEY environment variable not set.")
#         return None
    
#     endpoint = "/chemical/all"
#     headers = {'accept': 'application/json', 'x-api-key': api_key}
    
#     casrn_map = {}
#     offset = 1
#     page_num = 1
    
#     while True:
#         print(f"Fetching page {page_num} (offset {offset})... ", end="", flush=True)
#         params = {'next': offset,
#                   'projection': 'all-ids'}
#         response_data = _make_request('GET', endpoint, headers=headers, params=params)

#         chemicals_list = None
#         if isinstance(response_data, dict):
#             for value in response_data.values():
#                 if isinstance(value, list):
#                     chemicals_list = value
#                     break
        
#         if not chemicals_list:
#             print("Finished processing.")
#             break
            
#         for chemical in chemicals_list:
#             casrn = chemical.get('casrn')
#             dtxsid = chemical.get('dtxsid')
#             if casrn and dtxsid:
#                 if casrn not in casrn_map:
#                     # <-- THIS IS THE CORRECTED LINE
#                     casrn_map[casrn] = []
#                 if dtxsid not in casrn_map[casrn]:
#                     casrn_map[casrn].append(dtxsid)
        
#         processed_count = len(chemicals_list)
#         total_relationships = sum(len(ids) for ids in casrn_map.values())
#         print(
#             f"Processed {processed_count} chemicals. "
#             f"Total unique CASRNs: {len(casrn_map)}, "
#             f"Total relationships: {total_relationships}"
#         )

#         if processed_count < 1000:
#              print("Reached final page of results.")
#              break

#         offset += processed_count
#         page_num += 1
        
#     return casrn_map


def inspect_api_pages(num_pages=3):
    """
    Fetches and inspects the first few pages of the /chemical/all endpoint
    to help debug data structure issues, checking for duplicates across pages.

    Args:
        num_pages: The number of pages to fetch and inspect.
    """
    print(f"Inspecting first {num_pages} pages...")
    api_key = os.environ.get("EPA_API_KEY")
    if not api_key:
        print("Error: EPA_API_KEY environment variable not set.")
        return

    cumulative_map = {}
    offset = 1
    for i in range(num_pages):
        page_num = i + 1
        print(f"\n--- Fetching Page {page_num} (offset: {offset}) ---")
        endpoint = "/chemical/all"
        headers = {'accept': 'application/json', 'x-api-key': api_key}
        params = {'next': offset}
        response_data = _make_request('GET', endpoint, headers=headers, params=params)
        
        chemicals_list = None
        if isinstance(response_data, dict):
            for value in response_data.values():
                if isinstance(value, list):
                    chemicals_list = value
                    break
        
        if not chemicals_list:
            print("Could not find chemical list on this page.")
            break
        
        casrns_on_this_page = set()
        new_casrns_count = 0
        
        # Process this page's data
        for chemical in chemicals_list:
            casrn = chemical.get('casrn')
            dtxsid = chemical.get('dtxsid')
            if casrn and dtxsid:
                casrns_on_this_page.add(casrn)
                # Check if this CASRN is new to our cumulative map
                if casrn not in cumulative_map:
                    new_casrns_count += 1
                    cumulative_map[casrn] = []
                # Add the DTXSID if it's not already there
                if dtxsid not in cumulative_map[casrn]:
                    cumulative_map[casrn].append(dtxsid)
        
        print(f"Found {len(casrns_on_this_page)} unique CASRNs on this page.")
        print(f"Discovered {new_casrns_count} new CASRNs not seen on previous pages.")
        print(f"Cumulative map now contains {len(cumulative_map)} unique CASRNs.")
        
        offset += len(chemicals_list)

### -------------- ToxVal data harvest and processing --------------

def get_hazard_details(dtxsid: str):
    """
    Fetches ToxVal hazard data from the EPA CompTox API for a given DTXSID.
    Updated to resolve 404 error.
    """
    api_key = os.environ.get("EPA_API_KEY")
    if not api_key:
        print("Error: EPA_API_KEY environment variable not set.")
        return None
    
    # Updated endpoint path:
    endpoint = f"/hazard/toxval/search/by-dtxsid/{dtxsid}"
    
    headers = {
        'accept': 'application/json', 
        'x-api-key': api_key
    }
    
    return _make_request('GET', endpoint, headers=headers)

# def debug_hazard_endpoint(dtxsid):
#     api_key = os.environ.get("EPA_API_KEY")
#     # We will test the three most likely variations of the hazard path
#     variations = [
#         f"/hazard/toxval/search/by-dtxsid/{dtxsid}",
#         f"/hazard/toxval/details/search/by-dtxsid/{dtxsid}",
#         f"/hazard/toxval/summary/search/by-dtxsid/{dtxsid}"
#     ]
    
#     headers = {'accept': 'application/json', 'x-api-key': api_key}
    
#     for endpoint in variations:
#         print(f"\nTesting Endpoint: {endpoint}")
#         url = f"https://comptox.epa.gov/ctx-api{endpoint}"
#         try:
#             response = requests.get(url, headers=headers, timeout=30)
#             print(f"Status: {response.status_code}")
#             data = response.json()
#             if data:
#                 # If it's a list, show the count; if a dict, show keys
#                 count = len(data) if isinstance(data, list) else "1 (Dict)"
#                 print(f"SUCCESS: Found {count} records at this path.")
#                 return endpoint # Found the winner
#             else:
#                 print("Response returned 200 but body was empty [].")
#         except Exception as e:
#             print(f"Failed: {str(e)}")
#     return None


if __name__ == "__main__":
    # print(get_chemical_details())
    print(json.dumps(get_hazard_details('DTXSID3020596'), indent=2))

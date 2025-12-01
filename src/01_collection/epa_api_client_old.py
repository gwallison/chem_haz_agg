import os
import requests
import json
import argparse

# A list of potential base URLs for the API.
# The script will try them in order until one succeeds.
API_HOSTS = [
    "https://comptox.epa.gov/ctx-api",
    "https://api-ccte.epa.gov"
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

def get_dtxsid_by_casrn(casrn: str):
    """
    Fetches chemical details from the EPA CompTox API for a given CASRN.
    Note: This often returns a list, as one CASRN can map to multiple DTXSIDs.
    """
    api_key = os.environ.get("EPA_API_KEY")
    if not api_key:
        print("Error: EPA_API_KEY environment variable not set.")
        return None
    endpoint = f"/chemical/search/by-casrn/{casrn}"
    headers = {'accept': 'application/json', 'x-api-key': api_key}
    # Keep this query quiet to avoid flooding the console
    # print(f"\nQuerying API for CASRN: {casrn}...")
    return _make_request('GET', endpoint, headers=headers)



def get_dtxsids_by_casrns(casrns: list[str]):
    """
    Finds DTXSIDs for a given list of CASRN numbers.
    """
    api_key = os.environ.get("EPA_API_KEY")
    if not api_key:
        print("Error: EPA_API_KEY environment variable not set.")
        return None
    endpoint = "/chemical/batch"
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json',
        'x-api-key': api_key
    }
    payload = {"search_by": "casrn", "identifiers": casrns}
    print(f"Querying API for CASRNs: {', '.join(casrns)}...")
    return _make_request('POST', endpoint, headers=headers, data=json.dumps(payload))


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


def create_casrn_dtxsid_map():
    """
    Builds a dictionary mapping CASRNs to a list of DTXSIDs by fetching
    all chemicals from the API using pagination. This handles one-to-many
    relationships between CASRNs and DTXSIDs.
    
    Returns:
        A dictionary where keys are CASRNs and values are lists of DTXSIDs,
        or None on error.
    """
    api_key = os.environ.get("EPA_API_KEY")
    if not api_key:
        print("Error: EPA_API_KEY environment variable not set.")
        return None
    
    endpoint = "/chemical/all"
    headers = {'accept': 'application/json', 'x-api-key': api_key}
    
    casrn_map = {}
    offset = 1
    page_num = 1
    
    while True:
        print(f"Fetching page {page_num} (offset {offset})... ", end="", flush=True)
        params = {'next': offset,
                  'projection': 'all-ids'}
        response_data = _make_request('GET', endpoint, headers=headers, params=params)

        chemicals_list = None
        if isinstance(response_data, dict):
            for value in response_data.values():
                if isinstance(value, list):
                    chemicals_list = value
                    break
        
        if not chemicals_list:
            print("Finished processing.")
            break
            
        for chemical in chemicals_list:
            casrn = chemical.get('casrn')
            dtxsid = chemical.get('dtxsid')
            if casrn and dtxsid:
                if casrn not in casrn_map:
                    casrn_map[casrn] = []
                if dtxsid not in casrn_map[casrn]:
                    casrn_map[casrn].append(dtxsid)
        
        processed_count = len(chemicals_list)
        total_relationships = sum(len(ids) for ids in casrn_map.values())
        print(
            f"Processed {processed_count} chemicals. "
            f"Total unique CASRNs: {len(casrn_map)}, "
            f"Total relationships: {total_relationships}"
        )

        if processed_count < 1000:
             print("Reached the final page of results.")
             break

        offset += processed_count
        page_num += 1
        
    return casrn_map


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A command-line interface for the EPA CompTox API.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    parser_details = subparsers.add_parser("get-details", help="Fetch chemical details by DTXSID.")
    parser_details.add_argument("dtxsid", type=str, help="The DTXSID of the chemical (e.g., DTXSID7020182).")

    parser_casrn = subparsers.add_parser("get-dtxsids", help="Fetch DTXSIDs by CASRNs.")
    parser_casrn.add_argument("casrns", nargs='+', type=str, help="One or more CASRNs (e.g., 50-00-0 75-07-0).")
    
    parser_all = subparsers.add_parser("get-all-count", help="Get the total count of all chemicals in the database.")
    
    parser_map = subparsers.add_parser("create-map", help="Create a full CASRN to DTXSID map and return its size.")
    
    parser_inspect = subparsers.add_parser("inspect-pages", help="Fetch and inspect the maps for a few pages of data.")
    parser_inspect.add_argument("num_pages", type=int, nargs='?', default=3, help="The number of pages to fetch and inspect (default: 3).")


    args = parser.parse_args()

    if args.command == "get-details":
        data = get_chemical_details(args.dtxsid)
        if data:
            print("\n--- API Response ---")
            print(json.dumps(data, indent=2))
            
    elif args.command == "get-dtxsids":
        data = get_dtxsids_by_casrns(args.casrns)
        if data:
            print("\n--- API Response ---")
            print(json.dumps(data, indent=2))
            
    elif args.command == "get-all-count":
        count = get_all_chemicals_count()
        if count is not None:
            print(f"\nTotal number of chemicals found: {count}")
            
    elif args.command == "create-map":
        casrn_map = create_casrn_dtxsid_map()
        if casrn_map is not None:
            total_rels = sum(len(ids) for ids in casrn_map.values())
            print("\n--- Mapping Complete ---")
            print(f"Successfully created map with {len(casrn_map)} unique CASRNs and {total_rels} total relationships.")
            
    elif args.command == "inspect-pages":
        inspect_api_pages(args.num_pages)


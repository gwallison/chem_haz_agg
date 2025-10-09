# Import the specific functions you need from your client script.
import epa_api_client as eac

def main():
    """
    Example script to demonstrate using the epa_api_client module for debugging.
    """
    # Call the new inspect function to examine the first 5 pages of data.
    # print("Starting page inspection for debugging...")
    # eac.inspect_api_pages(num_pages=2)
    # print("\nPage inspection complete.")
    print(eac.get_chemical_details())

if __name__ == "__main__":
    main()



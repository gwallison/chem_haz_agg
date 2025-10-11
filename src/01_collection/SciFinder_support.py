# -*- coding: utf-8 -*-
"""
Created on Sat Oct 26 16:16:42 2024

@author: Gary
"""

from bs4 import BeautifulSoup

# fns =[ 
#       r"G:\My Drive\webshare\scrape_data\SciFinder_chem_pages\112926-00-8_SciFinder_collected_2024-11-23.html"
#       ]

def get_soup(fn):
    # Load the HTML file
    with open(fn, "r", encoding="utf-8") as f:
        html_doc = f.read()
    
    # Parse the HTML content
    return BeautifulSoup(html_doc, "html.parser")

def get_cas_from_filename(fstr):
    first = fstr.split('_')[0]
    if first.count('-') != 2:
        return ''
    else:
        return first

def get_cas_registry_number(soup):
  """
  Extracts the CAS Registry Number from the HTML.

  Args:
    soup: The BeautifulSoup object representing the parsed HTML.

  Returns:
    The CAS Registry Number as a string, or None if not found.
  """
  toolbar_title_element = soup.find("p", class_="toolbar-title")
  if toolbar_title_element:
    # First try to find the CAS number in a <mark> tag
    mark_element = toolbar_title_element.find("mark")
    if mark_element:
      return mark_element.text.strip()
    
    # If not found in <mark>, try finding it in a <span> tag
    span_element = toolbar_title_element.find("span")
    if span_element:
      # Extract the CAS number from the span's text 
      cas_number = span_element.text.split(":")[-1].strip()
      return cas_number
  return None

def get_preferred_registry_number(soup):
  """
  Extracts the Preferred Registry Number from the HTML, 
  regardless of whether it's in a <mark> tag or not.

  Args:
    soup: The BeautifulSoup object representing the parsed HTML.

  Returns:
    The Preferred Registry Number as a string, or None if not found.
  """
  preferred_rn_element = soup.find("div", class_="preferred-rn")
  if preferred_rn_element:
    # Try finding the <mark> tag first
    mark_element = preferred_rn_element.find("mark")
    if mark_element:
      return mark_element.text.strip()
    else:
      # If no <mark> tag, extract the number directly from the div's text
      preferred_rn = preferred_rn_element.text.split(":")[-1].strip()
      return preferred_rn
  return None

def get_substance_name(soup):
  """
  Extracts the substance name from the HTML.

  Args:
    soup: The BeautifulSoup object representing the parsed HTML.

  Returns:
    The substance name as a string, or None if not found.
  """
  substance_name_element = soup.find("div", class_="substance-name")
  if substance_name_element:
    return substance_name_element.text.strip()
  return None

def get_molecular_formula(soup):
  """
  Extracts the molecular formula from the HTML, removing any subscript tags.

  Args:
    soup: The BeautifulSoup object representing the parsed HTML.

  Returns:
    The molecular formula as a string, or None if not found.
  """
  molecular_formula_element = soup.find("h2", class_="molecular-formula")
  if molecular_formula_element:
    # Extract the text content, including the subscript tags
    formula_with_tags = molecular_formula_element.text.strip()
    
    # Remove the subscript tags ("<sub>" and "</sub>")
    formula_without_tags = formula_with_tags.replace("<sub>", "").replace("</sub>", "")
    
    return formula_without_tags
  return None

def get_substance_notes(soup):
  """
  Extracts the substance notes from the HTML.

  Args:
    soup: The BeautifulSoup object representing the parsed HTML.

  Returns:
    The substance notes as a string, or None if not found.
  """
  substance_notes_element = soup.find("span", class_="substanceNotes")
  if substance_notes_element:
    return substance_notes_element.text.strip()
  return None

def get_polymer_class_terms(soup):
  """
  Extracts the value of the "Polymer Class Terms" class from an HTML document.

  Args:
    html_doc: The HTML content as a string.

  Returns:
    The value of the "Polymer Class Terms" class as a string, or None if not found.
  """
  polymer_class_term_element = soup.find("div", class_="polymer-class-terms")
  if polymer_class_term_element:
    temp = polymer_class_term_element.text.strip()
    return temp.replace('Polymer Class Terms\n','')
  else:
    return None


def get_substance_classes(soup):
  """
  Extracts the substance classes from the HTML.

  Args:
    soup: The BeautifulSoup object representing the parsed HTML.

  Returns:
    A list of substance classes as strings, or an empty list if none are found.
  """
  substance_class_elements = soup.find("p", class_="substance-class")
  if substance_class_elements:
    temp = substance_class_elements.text.strip()
    out = []
    lst = temp.split(',')
    for i in lst:
        out.append(i.strip())
    return out
  return []

def get_number_of_references(soup):
  """
  Extracts the number of references from the HTML.

  Args:
    soup: The BeautifulSoup object representing the parsed HTML.

  Returns:
    The number of references as a string, or None if not found.
  """
  projection_count_element = soup.find("span", class_="projection-count")
  if projection_count_element:
    return projection_count_element.text.strip()
  return None



def get_number_of_components(soup):
  """
  Extracts the number of components from the HTML.

  Args:
    soup: The BeautifulSoup object representing the parsed HTML.

  Returns:
    The number of components as an integer, or None if not found.
  """
  num_components_element = soup.find("div", class_="num-components")
  if num_components_element:
    num_components_span = num_components_element.find("span", class_="numComponents")
    if num_components_span:
      try:
        return int(num_components_span.text.strip())
      except ValueError:
        return 'value error'
  return -1

def get_sub_component_substance_rn(soup):
  """
  Extracts the sub-component substance-rn values from the HTML.

  Args:
    soup: The BeautifulSoup object representing the parsed HTML.

  Returns:
    A list of sub-component substance-rn values as strings, 
    or an empty list if none are found.
  """
  substance_rn_elements = soup.find_all("p", class_="small sub-component substance-rn ng-star-inserted")
  if substance_rn_elements:
    return [element.text.strip() for element in substance_rn_elements]
  return []



def get_component_casrn_list(soup):
    """
    Extracts the list of Component RNs from the HTML. This occurs
    when the CAS numbers of the components are not in the compound image, 
    but rather under the name.

    Args:
      soup: The BeautifulSoup object representing the parsed HTML.

    Returns:
      A list of Component RNs as strings, or an empty list if none are found.
    """
    casrn_list = []
    for element in soup.find_all("div", class_=lambda value: value and all(
        x in value for x in ("substance-withoutSafsUri", "ng-star-inserted")
    )):
        if "Component RN:" in element.text:
            links = element.find_all("a")
            for link in links:
                casrn_list.append(link.text.strip())
    return casrn_list
def get_synonyms(soup):
  """
  Extracts the synonyms from the HTML.

  Args:
    soup: The BeautifulSoup object representing the parsed HTML.

  Returns:
    A list of synonyms as strings, or an empty list if none are found.
  """
  synonyms_element = soup.find("sf-substance-synonyms", class_="other-names")
  if synonyms_element:
    synonym_spans = synonyms_element.find_all("span")
    return [span.text.strip() for span in synonym_spans]
  return []

def get_deleted_registry_numbers(soup):
  """
  Extracts the deleted registry numbers from the HTML.

  Args:
    soup: The BeautifulSoup object representing the parsed HTML.

  Returns:
    A list of deleted registry numbers as strings, or an empty list if none are found.
  """
  deleted_rn_elements = soup.find_all("p", class_="substance-deleted-rn")
  if deleted_rn_elements:
    return [element.text.strip() for element in deleted_rn_elements]
  return []

def get_alternate_cas_numbers(soup):
  """
  Extracts the alternate CAS Registry Numbers from the HTML.

  Args:
    soup: The BeautifulSoup object representing the parsed HTML.

  Returns:
    A list of alternate CAS Registry Numbers as strings, 
    or an empty list if none are found.
  """
  alternate_cas_elements = soup.find_all("p", class_="substance-alternate-rn")
  if alternate_cas_elements:
    return [element.text.strip() for element in alternate_cas_elements]
  return []

if __name__ == '__main__':
    import os
    indir = r"C:\Users\Gary\My Drive\webshare\scrape_data\SciFinder_chem_pages"
    lst = os.listdir(indir)
    for fn in lst:
        if fn[-4:]!='html':
            continue
        soup = get_soup(os.path.join(indir,fn))
        print(get_cas_registry_number(soup))
        # print(get_substance_name(soup))
        print(get_sub_component_substance_rn(soup))
        print(get_component_casrn_list(soup))
        # print(get_number_of_references(soup))
        # print(get_substance_classes(soup))
        # print(get_alternate_cas_numbers(soup))
        # print(get_preferred_registry_number(soup))
        print('-------')
        
        
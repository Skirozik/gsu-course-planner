"""
Helper script to find major program pages in GSU catalog

Searches the catalog index to find navoid values for major programs.
"""

import requests
from bs4 import BeautifulSoup
import re


def search_catalog_index(catalog_id="42", search_term=""):
    """Search catalog index for major programs"""
    base_url = "https://catalogs.gsu.edu"

    # Try programs page
    url = f"{base_url}/content.php?catoid={catalog_id}&navoid=5314"

    print(f"Searching: {url}")
    print(f"Looking for: {search_term}\n")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all links
        links = soup.find_all('a', href=re.compile(r'navoid=\d+'))

        matches = []
        for link in links:
            text = link.get_text().strip()
            href = link.get('href', '')

            # Extract navoid
            navoid_match = re.search(r'navoid=(\d+)', href)
            if navoid_match:
                navoid = navoid_match.group(1)

                # Check if this matches our search
                if search_term.lower() in text.lower():
                    matches.append({
                        'text': text,
                        'navoid': navoid,
                        'url': f"{base_url}/{href}"
                    })

        return matches

    except Exception as e:
        print(f"Error: {e}")
        return []


def main():
    """Search for CIS and Health Science majors"""
    catalog_id = "42"

    print("=" * 70)
    print("FINDING MAJOR PROGRAM PAGES")
    print("=" * 70 + "\n")

    # Search for Computer Information Systems
    print("1. Searching for 'Computer Information Systems'...")
    cis_results = search_catalog_index(catalog_id, "computer information")

    if cis_results:
        print(f"Found {len(cis_results)} matches:")
        for result in cis_results:
            print(f"  - {result['text']}")
            print(f"    navoid: {result['navoid']}")
            print(f"    URL: {result['url']}\n")
    else:
        print("  No matches found\n")

    # Search for Health Science
    print("2. Searching for 'Health Science'...")
    health_results = search_catalog_index(catalog_id, "health science")

    if health_results:
        print(f"Found {len(health_results)} matches:")
        for result in health_results:
            print(f"  - {result['text']}")
            print(f"    navoid: {result['navoid']}")
            print(f"    URL: {result['url']}\n")
    else:
        print("  No matches found\n")

    # Also try broader search
    print("3. Searching for 'information systems'...")
    is_results = search_catalog_index(catalog_id, "information systems")

    if is_results:
        print(f"Found {len(is_results)} matches:")
        for result in is_results[:5]:  # Limit to first 5
            print(f"  - {result['text']}")
            print(f"    navoid: {result['navoid']}\n")


if __name__ == "__main__":
    main()

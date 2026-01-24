"""
GSU Course Schedule Scraper

Scrapes actual section data from GSU's course schedule to get real
professor assignments instead of using demo data.

Data Sources:
1. GSU PAWS/Banner (primary)
2. Public course schedule pages
3. Banner API if available

This replaces the demo generate_sample_sections() function.
"""

import requests
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional
import logging
import re
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class GSUScheduleScraper:
    """
    Scrapes GSU course schedule for real section data
    """

    # GSU Banner/Schedule URLs
    BASE_URL = "https://registration.gsu.edu"
    SCHEDULE_URL = f"{BASE_URL}/StudentRegistrationSsb/ssb/term/search"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=8"
    }

    REQUEST_DELAY = 1.0  # Be nice to GSU servers

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.last_request_time = 0
        self.cache = {}  # Cache scraped data

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    def get_current_term(self) -> str:
        """
        Get current term code (e.g., "202601" for Spring 2026)

        Format: YYYYTT where TT is:
        - 01 = Spring
        - 05 = Summer
        - 08 = Fall

        Returns:
            Term code string
        """
        now = datetime.now()
        year = now.year
        month = now.month

        # Determine term based on month
        if month <= 5:
            term = "01"  # Spring
        elif month <= 7:
            term = "05"  # Summer
        else:
            term = "08"  # Fall

        return f"{year}{term}"

    def search_course_sections(self,
                              subject: str,
                              course_number: str,
                              term: Optional[str] = None) -> List[Dict]:
        """
        Search for course sections

        Args:
            subject: Department code (e.g., "CSC", "MATH")
            course_number: Course number (e.g., "3320")
            term: Term code (defaults to current term)

        Returns:
            List of section dicts with instructor info
        """
        if term is None:
            term = self.get_current_term()

        # Check cache first
        cache_key = f"{term}_{subject}_{course_number}"
        if cache_key in self.cache:
            logger.info(f"Cache hit for {cache_key}")
            return self.cache[cache_key]

        logger.info(f"Scraping sections for {subject} {course_number} in term {term}")

        try:
            self._rate_limit()

            # GSU uses different URL structures - this is a template
            # You'll need to inspect GSU's actual registration site
            url = f"{self.SCHEDULE_URL}?term={term}&subject={subject}&courseNumber={course_number}"

            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch schedule: {response.status_code}")
                return []

            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')

            sections = self._parse_sections(soup, subject, course_number)

            # Cache results
            self.cache[cache_key] = sections

            return sections

        except Exception as e:
            logger.error(f"Error scraping GSU schedule: {e}")
            return []

    def _parse_sections(self, soup: BeautifulSoup, subject: str, course_number: str) -> List[Dict]:
        """
        Parse section data from HTML

        NOTE: This is a TEMPLATE - you need to inspect GSU's actual HTML structure
        and update the selectors accordingly.

        Args:
            soup: BeautifulSoup object
            subject: Department code
            course_number: Course number

        Returns:
            List of section dicts
        """
        sections = []

        # EXAMPLE - Update these selectors based on actual GSU HTML
        # You'll need to inspect the page source
        section_rows = soup.find_all('tr', class_='section-row')  # Example class

        for row in section_rows:
            try:
                # Extract section data - UPDATE THESE SELECTORS
                section_num = row.find('td', class_='section').text.strip()
                crn = row.find('td', class_='crn').text.strip()
                instructor = row.find('td', class_='instructor').text.strip()
                time_info = row.find('td', class_='time').text.strip()
                location = row.find('td', class_='location').text.strip()
                seats_avail = row.find('td', class_='seats').text.strip()

                sections.append({
                    "section": section_num,
                    "crn": crn,
                    "instructor": instructor,
                    "course_code": f"{subject} {course_number}",
                    "time": time_info,
                    "location": location,
                    "seats_available": seats_avail,
                    "term": self.get_current_term()
                })

            except Exception as e:
                logger.warning(f"Error parsing section row: {e}")
                continue

        return sections

    def get_all_sections_for_courses(self,
                                    course_codes: List[str],
                                    term: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Get sections for multiple courses

        Args:
            course_codes: List of course codes (e.g., ["CSC 3320", "MATH 2420"])
            term: Term code

        Returns:
            Dict mapping course codes to section lists
        """
        results = {}

        for course_code in course_codes:
            # Parse course code
            parts = course_code.split()
            if len(parts) != 2:
                logger.warning(f"Invalid course code: {course_code}")
                continue

            subject = parts[0]
            course_number = parts[1]

            sections = self.search_course_sections(subject, course_number, term)
            results[course_code] = sections

            # Be nice to servers
            time.sleep(0.5)

        return results


# Alternative: Parse from downloaded HTML files
def parse_schedule_from_html_file(html_file_path: str) -> List[Dict]:
    """
    Parse section data from a saved HTML file

    Useful if you manually download course schedule pages.

    Args:
        html_file_path: Path to HTML file

    Returns:
        List of section dicts
    """
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Parse sections - update selectors based on actual HTML
    sections = []
    # ... parsing logic here ...

    return sections


# Alternative: Use Banner API if available
class BannerAPIClient:
    """
    Client for Banner/Ellucian API if GSU provides one

    Some universities expose a JSON API for course data.
    Check if GSU has a public API endpoint.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.gsu.edu/banner"  # Example - check actual URL

    def get_sections(self, term: str, subject: str, course_number: str) -> List[Dict]:
        """
        Get sections from Banner API

        Args:
            term: Term code
            subject: Department code
            course_number: Course number

        Returns:
            List of section dicts
        """
        # Example API request
        url = f"{self.base_url}/sections"
        params = {
            "term": term,
            "subject": subject,
            "courseNumber": course_number
        }

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            return []


# HOW TO USE:

def get_real_sections(course_code: str, term: Optional[str] = None) -> List[Dict]:
    """
    Get real sections from GSU schedule

    This replaces generate_sample_sections() in app.py

    Args:
        course_code: Course code (e.g., "CSC 3320")
        term: Term code (optional)

    Returns:
        List of section dicts ready for ranking
    """
    scraper = GSUScheduleScraper()

    # Parse course code
    parts = course_code.split()
    if len(parts) != 2:
        return []

    subject = parts[0]
    course_number = parts[1]

    sections = scraper.search_course_sections(subject, course_number, term)

    return sections


# Example usage
if __name__ == "__main__":
    print("Testing GSU Schedule Scraper...")
    print("=" * 70)

    # This is a template - you need to:
    # 1. Inspect GSU's actual registration site
    # 2. Update BASE_URL and selectors
    # 3. Test with real data

    scraper = GSUScheduleScraper()

    # Test getting current term
    current_term = scraper.get_current_term()
    print(f"Current term: {current_term}")

    # Test scraping (will fail until you update URLs/selectors)
    print("\nAttempting to scrape CSC 3320...")
    sections = scraper.search_course_sections("CSC", "3320")

    if sections:
        print(f"Found {len(sections)} sections:")
        for section in sections:
            print(f"  Section {section['section']}: {section['instructor']}")
    else:
        print("No sections found (need to update scraper for actual GSU site)")

    print("\n" + "=" * 70)
    print("NEXT STEPS:")
    print("1. Visit: https://registration.gsu.edu")
    print("2. Inspect HTML structure of course schedule")
    print("3. Update selectors in _parse_sections()")
    print("4. Test with real course data")
    print("5. Replace generate_sample_sections() in app.py")

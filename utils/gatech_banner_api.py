"""
Georgia Tech Banner API Client

Calls Georgia Tech's Banner/Ellucian API directly to get real-time course data.
This is MUCH better than scraping HTML - we get clean JSON data.

Base URL: https://registration.banner.gatech.edu/StudentRegistrationSsb
"""

import requests
import json
from typing import List, Dict, Optional
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.WARNING)  # Only show warnings/errors in production
logger = logging.getLogger(__name__)


class GATechBannerAPI:
    """
    Client for Georgia Tech Banner/Ellucian Self-Service API
    """

    BASE_URL = "https://registration.banner.gatech.edu/StudentRegistrationSsb"

    # API endpoints (same structure as GSU)
    TERM_SELECTION = f"{BASE_URL}/ssb/term/search?mode=search"
    SEARCH_ENDPOINT = f"{BASE_URL}/ssb/classSearch/classSearch"
    RESULTS_ENDPOINT = f"{BASE_URL}/ssb/searchResults/searchResults"
    SECTION_DETAILS = f"{BASE_URL}/ssb/searchResults/getSectionDetail"
    FACULTY_TIMES = f"{BASE_URL}/ssb/searchResults/getFacultyMeetingTimes"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest"  # Important for AJAX calls
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self.last_request_time = 0

    def _rate_limit(self, delay=0.5):
        """Be nice to Georgia Tech servers"""
        elapsed = time.time() - self.last_request_time
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self.last_request_time = time.time()

    def get_current_term(self) -> str:
        """
        Get current term code for Georgia Tech

        Format: YYYYMM where:
        - 202601 = Spring 2026
        - 202605 = Summer 2026
        - 202608 = Fall 2026
        """
        now = datetime.now()
        year = now.year
        month = now.month

        if month <= 5:
            term_code = "01"  # Spring
        elif month <= 7:
            term_code = "05"  # Summer
        else:
            term_code = "08"  # Fall

        return f"{year}{term_code}"

    def select_term(self, term: str) -> bool:
        """
        Submit term selection to Banner (required before searching)

        Args:
            term: Term code (e.g., "202601")

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Selecting term {term}")

        try:
            self._rate_limit()

            # POST the term selection
            payload = {
                "term": term,
                "studyPath": "",
                "studyPathText": "",
                "startDatepicker": "",
                "endDatepicker": ""
            }

            response = self.session.post(
                self.TERM_SELECTION,
                data=payload,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"Term {term} selected successfully")
                return True
            else:
                logger.error(f"Failed to select term: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error selecting term: {e}")
            return False

    def search_courses(self,
                      term: str,
                      subject: str = "CS",
                      page_max_size: int = 500,
                      page_offset: int = 0) -> List[Dict]:
        """
        Search for courses using Banner API

        Args:
            term: Term code (e.g., "202601")
            subject: Subject code (e.g., "CS", "MATH")
            page_max_size: Max results per page
            page_offset: Pagination offset

        Returns:
            List of course section dicts with all details
        """
        logger.info(f"Searching {subject} courses for term {term}")

        # First, submit term selection (required by Banner)
        if not self.select_term(term):
            logger.error("Failed to select term, cannot search")
            return []

        # Payload for POST request (Banner uses POST for searches)
        payload = {
            "txt_term": term,
            "txt_subject": subject,
            "pageOffset": page_offset,
            "pageMaxSize": page_max_size,
            "sortColumn": "subjectDescription",
            "sortDirection": "asc"
        }

        try:
            self._rate_limit()

            response = self.session.post(
                self.RESULTS_ENDPOINT,
                data=payload,
                timeout=15
            )

            if response.status_code != 200:
                logger.error(f"API returned status {response.status_code}")
                logger.error(f"Response: {response.text[:500]}")
                return []

            # Parse JSON response
            data = response.json()

            if not data or "data" not in data:
                logger.warning("No data in response")
                return []

            courses = data["data"]

            if courses is None:
                logger.warning("courses is None")
                return []

            logger.info(f"Found {len(courses)} sections")

            return courses

        except Exception as e:
            logger.error(f"Error calling Banner API: {e}")
            import traceback
            traceback.print_exc()
            return []

    def get_section_details(self, term: str, crn: str) -> Optional[Dict]:
        """
        Get detailed info for a specific section

        Args:
            term: Term code
            crn: Course Registration Number

        Returns:
            Section details dict or None
        """
        logger.info(f"Fetching details for CRN {crn}")

        payload = {
            "term": term,
            "courseReferenceNumber": crn
        }

        try:
            self._rate_limit()

            response = self.session.post(
                self.FACULTY_TIMES,
                data=payload,
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to get details for CRN {crn}")
                return None

        except Exception as e:
            logger.error(f"Error fetching section details: {e}")
            return None

    def extract_section_data(self, raw_section: Dict) -> Dict:
        """
        Extract clean section data from Banner API response

        Args:
            raw_section: Raw section dict from API

        Returns:
            Cleaned section dict ready for ranking
        """
        # Extract instructor names (Banner stores as list)
        instructors = raw_section.get("faculty", [])
        instructor_name = "Staff"

        if instructors and len(instructors) > 0:
            primary_instructor = instructors[0]
            display_name = primary_instructor.get("displayName", "Staff")
            instructor_name = display_name if display_name != "TBA" else "Staff"

        # Extract meeting times
        meetings = raw_section.get("meetingsFaculty", [])
        time_str = "TBA"
        days_str = ""
        location = "TBA"

        if meetings and len(meetings) > 0:
            first_meeting = meetings[0]
            meeting_time = first_meeting.get("meetingTime", {})

            begin_time = meeting_time.get("beginTime")
            end_time = meeting_time.get("endTime")

            if begin_time and end_time:
                time_str = f"{begin_time}-{end_time}"

            # Days of week
            days = []
            if meeting_time.get("monday"): days.append("M")
            if meeting_time.get("tuesday"): days.append("T")
            if meeting_time.get("wednesday"): days.append("W")
            if meeting_time.get("thursday"): days.append("Th")
            if meeting_time.get("friday"): days.append("F")
            if meeting_time.get("saturday"): days.append("Sa")
            if meeting_time.get("sunday"): days.append("Su")

            days_str = "".join(days) if days else "TBA"

            # Location
            building = meeting_time.get("building", "")
            room = meeting_time.get("room", "")
            if building and room:
                location = f"{building} {room}"
            elif building:
                location = building

        # Build clean section dict
        section_data = {
            "section": raw_section.get("sequenceNumber", "001"),
            "crn": raw_section.get("courseReferenceNumber", ""),
            "instructor": instructor_name,
            "course_code": f"{raw_section.get('subject', '')} {raw_section.get('courseNumber', '')}",
            "course_title": raw_section.get("courseTitle", ""),
            "time": time_str,
            "days": days_str,
            "location": location,
            "seats_available": raw_section.get("seatsAvailable", 0),
            "seats_total": raw_section.get("maximumEnrollment", 0),
            "waitlist_available": raw_section.get("waitAvailable", 0),
            "credits": raw_section.get("creditHourLow", 3),
            "campus": raw_section.get("campusDescription", "Atlanta"),
            "instructional_method": raw_section.get("instructionalMethod", "Lecture"),
            "term": raw_section.get("term", "")
        }

        return section_data

    def get_all_sections(self, term: str, subject: str) -> List[Dict]:
        """
        Get all sections for a subject, properly formatted

        Args:
            term: Term code
            subject: Subject (e.g., "CS")

        Returns:
            List of formatted section dicts
        """
        # Get raw data from API
        raw_sections = self.search_courses(term, subject)

        if not raw_sections:
            logger.warning(f"No sections found for {subject}")
            return []

        # Clean and format each section
        formatted_sections = []
        for raw_section in raw_sections:
            try:
                formatted = self.extract_section_data(raw_section)
                formatted_sections.append(formatted)
            except Exception as e:
                logger.error(f"Error formatting section: {e}")
                continue

        return formatted_sections


def get_gatech_sections(course_code: str, term: Optional[str] = None) -> List[Dict]:
    """
    Main function: Get real Georgia Tech sections for a course

    This REPLACES generate_sample_sections() in app.py for GT students

    Args:
        course_code: Course code (e.g., "CS 1332")
        term: Term code (optional, defaults to current)

    Returns:
        List of section dicts ready for ranking
    """
    api = GATechBannerAPI()

    if term is None:
        term = api.get_current_term()

    # Parse course code
    parts = course_code.split()
    if len(parts) != 2:
        logger.error(f"Invalid course code: {course_code}")
        return []

    subject = parts[0]

    # Get all sections for the subject
    all_sections = api.get_all_sections(term, subject)

    # Filter to exactly this course (whitespace/case-insensitive full-code match).
    # A substring match would wrongly include e.g. CS 1331 when asked for CS 1301.
    def _norm(code: str) -> str:
        return "".join(str(code).split()).upper()

    target = _norm(course_code)
    course_sections = [
        s for s in all_sections
        if _norm(s.get("course_code", "")) == target
    ]

    logger.info(f"Found {len(course_sections)} sections for {course_code}")

    return course_sections


# Example usage / testing
if __name__ == "__main__":
    print("=" * 70)
    print("Georgia Tech Banner API - Live Course Data")
    print("=" * 70)

    api = GATechBannerAPI()

    # Get current term
    current_term = api.get_current_term()
    print(f"\nCurrent term: {current_term}")

    # Try multiple terms to find one with data
    test_terms = [
        current_term,  # Spring 2026: 202601
        "202508",      # Fall 2025
        "202505",      # Summer 2025
        "202501",      # Spring 2025
    ]

    print(f"\nTesting multiple terms to find course data...")
    for term in test_terms:
        print(f"  Trying term {term}...", end=" ")
        test_sections = api.search_courses(term, "CS")
        if test_sections and len(test_sections) > 0:
            print(f"✅ Found {len(test_sections)} CS sections!")
            current_term = term
            break
        else:
            print(f"No data")

    # Test: Get CS 1332 sections
    print(f"\nFetching CS 1332 sections for term {current_term}...")

    sections = get_gatech_sections("CS 1332", current_term)

    if sections:
        print(f"\n✅ Found {len(sections)} sections for CS 1332:\n")

        for section in sections[:5]:  # Show first 5
            print(f"Section {section['section']} (CRN: {section['crn']})")
            print(f"  Instructor: {section['instructor']}")
            print(f"  Time: {section['days']} {section['time']}")
            print(f"  Location: {section['location']}")
            print(f"  Seats: {section['seats_available']}/{section['seats_total']}")
            print()

        # Save to file
        output_file = "data/gatech_sections_real.json"
        import os
        os.makedirs("data", exist_ok=True)

        with open(output_file, 'w') as f:
            json.dump(sections, f, indent=2)

        print(f"✅ Saved to {output_file}")

    else:
        print("❌ No sections found")
        print("\nPossible reasons:")
        print("1. Term code might be wrong")
        print("2. Course not offered this term")
        print("3. Need to be logged in to Georgia Tech")
        print("4. API endpoint changed")

    print("\n" + "=" * 70)

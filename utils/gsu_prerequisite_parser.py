"""
GSU Prerequisite Parser - Modern Campus Catalog
Scrapes course-level prerequisites from Georgia State University's public catalog.

Objectives:
- Extract prerequisites, corequisites, and restrictions EXACTLY as written
- Use deterministic DOM selectors for reliability
- Handle errors gracefully
- Support extensibility to other departments

Department: Computer Science (CSC) - 2025-2026 Undergraduate Catalog
Source: https://catalogs.gsu.edu (Modern Campus Catalog)
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class CourseData:
    """Data class for parsed course information"""
    course_code: str
    title: str
    credits: int
    prerequisites_raw: str = ""  # Exact catalog text
    corequisites_raw: str = ""   # Exact catalog text
    restrictions_raw: str = ""    # Exact catalog text (e.g., major eligibility)
    description: str = ""
    coid: str = ""  # Modern Campus course ID


class GSUPrerequisiteParser:
    """
    Parser for GSU Modern Campus Catalog prerequisite information.

    Features:
    - Deterministic HTML selectors
    - Rate limiting (1 request per second)
    - Graceful error handling
    - Extensible to other departments
    """

    BASE_URL = "https://catalogs.gsu.edu"
    CATALOG_ID = "42"  # 2025-2026 catalog

    # User-agent to identify ourselves
    HEADERS = {
        "User-Agent": "GSU-Course-Planner-Bot/1.0 (Academic Planning Tool; +https://github.com/Skirozik/gsu-course-planner)"
    }

    # Rate limiting: 1 request per second
    REQUEST_DELAY = 1.0

    def __init__(self, catalog_id: str = "42"):
        """
        Initialize parser with specific catalog year.

        Args:
            catalog_id: Modern Campus catalog ID (default: 42 for 2025-2026)
        """
        self.catalog_id = catalog_id
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    def _safe_request(self, url: str) -> Optional[BeautifulSoup]:
        """
        Make a rate-limited HTTP request with error handling.

        Args:
            url: Full URL to fetch

        Returns:
            BeautifulSoup object or None on error
        """
        self._rate_limit()

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_course_list(self, department_code: str) -> List[Dict[str, str]]:
        """
        Get list of all courses for a department from the catalog.

        Args:
            department_code: Department prefix (e.g., 'CSC', 'MATH')

        Returns:
            List of dicts with 'course_code', 'title', 'coid', 'url'
        """
        # Try multiple strategies to find courses

        # Strategy 1: Direct course listing page (if it exists)
        listing_url = f"{self.BASE_URL}/content.php?catoid={self.catalog_id}&navoid=5314"
        soup = self._safe_request(listing_url)

        if not soup:
            return []

        courses = []

        # Find all course links - Modern Campus uses this pattern
        # <a href="preview_course_nopop.php?catoid=X&coid=Y">DEPT ####  - Course Title</a>
        course_links = soup.find_all('a', href=re.compile(r'preview_course_nopop\.php\?catoid=\d+&coid=\d+'))

        for link in course_links:
            text = link.get_text().strip()

            # Match course code pattern (e.g., "CSC 1301 - Title")
            match = re.match(rf'^({department_code}\s+\d{{4}}[A-Z]?)\s*-\s*(.+)$', text, re.IGNORECASE)

            if match:
                course_code = match.group(1).strip()
                title = match.group(2).strip()

                # Extract coid from URL
                coid_match = re.search(r'coid=(\d+)', link.get('href', ''))
                coid = coid_match.group(1) if coid_match else ""

                courses.append({
                    'course_code': course_code,
                    'title': title,
                    'coid': coid,
                    'url': f"{self.BASE_URL}/preview_course_nopop.php?catoid={self.catalog_id}&coid={coid}"
                })

        # Filter to just the specified department
        courses = [c for c in courses if c['course_code'].upper().startswith(department_code.upper())]

        print(f"Found {len(courses)} {department_code} courses")
        return courses

    def parse_course_detail(self, coid: str, course_code: str = "") -> Optional[CourseData]:
        """
        Parse detailed course information from individual course page.

        Uses deterministic selectors and text patterns to extract:
        - Course code and title
        - Credit hours
        - Prerequisites (exact text)
        - Corequisites (exact text)
        - Restrictions (exact text)

        Args:
            coid: Modern Campus course ID
            course_code: Optional course code for logging

        Returns:
            CourseData object or None on error
        """
        url = f"{self.BASE_URL}/preview_course_nopop.php?catoid={self.catalog_id}&coid={coid}"
        soup = self._safe_request(url)

        if not soup:
            return None

        try:
            # Extract course code and title from H1 with id='course_preview_title'
            # Format: "CSC 1301 - Principles of Computer Science I"
            h1 = soup.find('h1', id='course_preview_title')
            if not h1:
                print(f"Warning: No course title H1 found for coid={coid}")
                return None

            h1_text = h1.get_text().strip()
            match = re.match(r'^([A-Z]{2,4}\s+\d{4}[A-Z]?)\s*-\s*(.+)$', h1_text)

            if not match:
                print(f"Warning: Could not parse H1 text: {h1_text}")
                return None

            parsed_course_code = match.group(1).strip()
            title = match.group(2).strip()

            # Extract all text content for pattern matching
            page_text = soup.get_text()

            # Extract credit hours
            # Pattern: "4 Credit Hours" or "3-4 Credit Hours"
            credits = 0
            credit_match = re.search(r'(\d+(?:-\d+)?)\s+Credit\s+Hours?', page_text, re.IGNORECASE)
            if credit_match:
                credit_str = credit_match.group(1)
                # Handle range (take minimum)
                if '-' in credit_str:
                    credits = int(credit_str.split('-')[0])
                else:
                    credits = int(credit_str)

            # Extract prerequisites - exact text as written
            # Stop at keywords like "Description", "Back to Top", or next bold section
            prerequisites_raw = ""
            prereq_patterns = [
                r'Prerequisite[s]?:\s*(.+?)(?=\s+(?:Description|Back to Top|Corequisite|Requirements?|Restrictions?|$))',
                r'Pre-requisite[s]?:\s*(.+?)(?=\s+(?:Description|Back to Top|Corequisite|Requirements?|Restrictions?|$))',
                r'Pre/Corequisite[s]?:\s*(.+?)(?=\s+(?:Description|Back to Top|Requirements?|Restrictions?|$))',
            ]

            for pattern in prereq_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                if match:
                    prerequisites_raw = match.group(1).strip()
                    # Clean up extra whitespace but preserve structure
                    prerequisites_raw = re.sub(r'\s+', ' ', prerequisites_raw)
                    # Remove trailing periods or junk
                    prerequisites_raw = re.sub(r'\s*\.\s*$', '', prerequisites_raw)
                    break

            # Extract corequisites - exact text as written
            corequisites_raw = ""
            coreq_patterns = [
                r'Corequisite[s]?:\s*([^\n]+)',
                r'Co-requisite[s]?:\s*([^\n]+)',
            ]

            for pattern in coreq_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    corequisites_raw = match.group(1).strip()
                    corequisites_raw = re.sub(r'\s+', ' ', corequisites_raw)
                    break

            # Extract restrictions - exact text as written
            # Stop at keywords like "Description", "Back to Top", or next section
            restrictions_raw = ""
            restriction_patterns = [
                r'Requirements?:\s*(.+?)(?=\s+(?:Description|Back to Top|Prerequisite|Corequisite|$))',
                r'Restrictions?:\s*(.+?)(?=\s+(?:Description|Back to Top|Prerequisite|Corequisite|$))',
                r'Enrollment\s+(?:limited|restricted)\s+to:\s*(.+?)(?=\s+(?:Description|Back to Top|Prerequisite|Corequisite|$))',
            ]

            for pattern in restriction_patterns:
                match = re.search(pattern, page_text, re.IGNORECASE | re.DOTALL)
                if match:
                    restrictions_raw = match.group(1).strip()
                    restrictions_raw = re.sub(r'\s+', ' ', restrictions_raw)
                    # Remove trailing periods
                    restrictions_raw = re.sub(r'\s*\.\s*$', '', restrictions_raw)
                    break

            # Extract description (first paragraph after title, excluding requirements)
            description = ""
            # Find text between title and first requirement keyword
            desc_match = re.search(
                rf'{re.escape(title)}.*?(\d+\s+Credit\s+Hours?)\s*(.+?)(?=(?:Prerequisite|Corequisite|Requirements?|Restrictions?):|\*\*|$)',
                page_text,
                re.IGNORECASE | re.DOTALL
            )
            if desc_match:
                description = desc_match.group(2).strip()
                description = re.sub(r'\s+', ' ', description)[:500]  # Limit length

            return CourseData(
                course_code=parsed_course_code,
                title=title,
                credits=credits,
                prerequisites_raw=prerequisites_raw,
                corequisites_raw=corequisites_raw,
                restrictions_raw=restrictions_raw,
                description=description,
                coid=coid
            )

        except Exception as e:
            print(f"Error parsing course detail for coid={coid}: {e}")
            return None

    def scrape_department(self, department_code: str) -> List[CourseData]:
        """
        Scrape all courses for a department.

        Args:
            department_code: Department prefix (e.g., 'CSC')

        Returns:
            List of CourseData objects
        """
        print(f"\nScraping {department_code} courses from GSU Catalog {self.catalog_id}...")

        # Get course list
        course_list = self.get_course_list(department_code)

        if not course_list:
            print(f"No courses found for {department_code}")
            return []

        # Parse each course
        parsed_courses = []

        for i, course_info in enumerate(course_list, 1):
            print(f"[{i}/{len(course_list)}] Parsing {course_info['course_code']}...")

            course_data = self.parse_course_detail(
                coid=course_info['coid'],
                course_code=course_info['course_code']
            )

            if course_data:
                parsed_courses.append(course_data)
            else:
                print(f"  ⚠ Failed to parse {course_info['course_code']}")

        print(f"\n✓ Successfully parsed {len(parsed_courses)}/{len(course_list)} courses")
        return parsed_courses

    def save_to_json(self, courses: List[CourseData], output_file: str):
        """
        Save parsed courses to JSON file.

        Args:
            courses: List of CourseData objects
            output_file: Path to output JSON file
        """
        data = [asdict(course) for course in courses]

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved {len(courses)} courses to {output_file}")


def main():
    """Example usage: Scrape CSC courses"""
    parser = GSUPrerequisiteParser(catalog_id="38")

    # Scrape Computer Science courses
    csc_courses = parser.scrape_department("CSC")

    # Save to JSON
    if csc_courses:
        parser.save_to_json(
            csc_courses,
            "data/parsed_prerequisites/csc_prerequisites_catalog_38.json"
        )

        # Print sample courses for validation
        print("\n" + "="*60)
        print("SAMPLE PARSED COURSES (First 3)")
        print("="*60)

        for course in csc_courses[:3]:
            print(f"\n{course.course_code} - {course.title}")
            print(f"  Credits: {course.credits}")
            if course.prerequisites_raw:
                print(f"  Prerequisites: {course.prerequisites_raw}")
            if course.corequisites_raw:
                print(f"  Corequisites: {course.corequisites_raw}")
            if course.restrictions_raw:
                print(f"  Restrictions: {course.restrictions_raw}")


if __name__ == "__main__":
    main()

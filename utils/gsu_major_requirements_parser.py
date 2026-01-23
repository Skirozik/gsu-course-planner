"""
GSU Major Requirements Parser - Modern Campus Catalog

Scrapes major program requirements from Georgia State University's public catalog.

Objectives:
- Extract major degree requirements structure
- Preserve groupings and raw text
- Support multiple majors with consistent format
- Integrate with existing course data

Source: GSU Modern Campus Catalog - Major Program Pages
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class MajorRequirements:
    """Data class for parsed major requirements"""
    major_name: str
    degree_type: str  # e.g., "B.S.", "B.A."
    college: str
    catalog_year: str
    total_hours: int
    required_courses: Dict[str, List[str]]  # Category -> course codes
    elective_groups: List[Dict[str, any]]
    progression_notes: str  # Raw text
    restrictions: str  # Raw text
    source_url: str
    parsed_date: str = ""


class GSUMajorRequirementsParser:
    """
    Parser for GSU Modern Campus Catalog major program requirements.

    Features:
    - Parses major program pages (not individual course pages)
    - Extracts requirement categories and course lists
    - Preserves structure and raw text
    - Extensible to additional majors
    """

    BASE_URL = "https://catalogs.gsu.edu"
    CATALOG_ID = "42"  # 2025-2026 catalog

    HEADERS = {
        "User-Agent": "GSU-Course-Planner-Bot/1.0 (Academic Planning Tool; +https://github.com/Skirozik/gsu-course-planner)"
    }

    REQUEST_DELAY = 1.0

    # Known major page IDs (poid) in catalog 42
    MAJOR_PAGES = {
        "Computer Information Systems": {
            "poid": "12246",
            "degree_type": "B.B.A.",
            "college": "J. Mack Robinson College of Business"
        },
        "Health Sciences": {
            "poid": "12238",
            "degree_type": "B.I.S.",
            "college": "Byrdine F. Lewis College of Nursing and Health Professions"
        }
    }

    def __init__(self, catalog_id: str = "42"):
        """Initialize parser with catalog year"""
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
        """Make a rate-limited HTTP request with error handling"""
        self._rate_limit()

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def search_major_page(self, major_name: str) -> Optional[str]:
        """
        Search for major program page by name.
        Returns poid if found.
        """
        # Try known page first
        if major_name in self.MAJOR_PAGES:
            return self.MAJOR_PAGES[major_name]["poid"]

        # Otherwise would need to search the catalog index
        # For now, return None
        return None

    def parse_major_requirements(self, major_name: str, poid: str = None) -> Optional[MajorRequirements]:
        """
        Parse major requirements from program page.

        Args:
            major_name: Name of the major
            poid: Program object ID for the major page

        Returns:
            MajorRequirements object or None on error
        """
        if poid is None:
            poid = self.search_major_page(major_name)

        if not poid:
            print(f"Could not find page for major: {major_name}")
            return None

        url = f"{self.BASE_URL}/preview_program.php?catoid={self.catalog_id}&poid={poid}"
        soup = self._safe_request(url)

        if not soup:
            return None

        try:
            # Extract page content - try multiple possible containers
            content = (
                soup.find('td', class_='block_content') or
                soup.find('div', class_='acalog-core') or
                soup.find('div', id='contentarea') or
                soup.find('div', class_='page_content')
            )

            if not content:
                print(f"Could not find content area for {major_name}")
                return None

            page_text = content.get_text()

            # Extract metadata
            degree_type = self._extract_degree_type(page_text, major_name)
            college = self._extract_college(page_text, major_name)
            total_hours = self._extract_total_hours(page_text)

            # Extract course requirements
            required_courses = self._extract_required_courses(content)

            # Extract elective groups
            elective_groups = self._extract_elective_groups(content)

            # Extract progression notes
            progression_notes = self._extract_progression_notes(page_text)

            # Extract restrictions
            restrictions = self._extract_restrictions(page_text)

            return MajorRequirements(
                major_name=major_name,
                degree_type=degree_type,
                college=college,
                catalog_year="2025-2026",
                total_hours=total_hours,
                required_courses=required_courses,
                elective_groups=elective_groups,
                progression_notes=progression_notes,
                restrictions=restrictions,
                source_url=url
            )

        except Exception as e:
            print(f"Error parsing major requirements for {major_name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_degree_type(self, text: str, major_name: str) -> str:
        """Extract degree type (B.S., B.A., etc.)"""
        # Check known majors first
        if major_name in self.MAJOR_PAGES:
            return self.MAJOR_PAGES[major_name]["degree_type"]

        # Try to find in text
        match = re.search(r'(B\.S\.|B\.A\.|Bachelor of Science|Bachelor of Arts)', text, re.IGNORECASE)
        if match:
            degree_text = match.group(1)
            if 'science' in degree_text.lower() or degree_text == 'B.S.':
                return "B.S."
            elif 'arts' in degree_text.lower() or degree_text == 'B.A.':
                return "B.A."

        return "B.S."  # Default

    def _extract_college(self, text: str, major_name: str) -> str:
        """Extract college name"""
        if major_name in self.MAJOR_PAGES:
            return self.MAJOR_PAGES[major_name]["college"]

        # Try to find in text
        college_match = re.search(r'College of ([A-Za-z\s&]+)', text)
        if college_match:
            return f"College of {college_match.group(1).strip()}"

        return "Unknown College"

    def _extract_total_hours(self, text: str) -> int:
        """Extract total credit hours required"""
        # Look for patterns like "120 hours" or "Total: 120"
        patterns = [
            r'Total[:\s]+(\d{2,3})\s+(?:credit\s+)?hours?',
            r'(\d{2,3})\s+(?:total\s+)?(?:credit\s+)?hours?\s+required',
            r'minimum\s+of\s+(\d{2,3})\s+hours?'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return 120  # Default

    def _extract_required_courses(self, content) -> Dict[str, List[str]]:
        """
        Extract required courses organized by category.

        Returns dict of category -> list of course codes
        """
        required = {}

        # Look for common section headers
        sections = content.find_all(['h2', 'h3', 'h4', 'p', 'div'])

        current_category = "Core Requirements"
        course_pattern = re.compile(r'\b([A-Z]{2,4})\s+(\d{4}[A-Z]?)\b')

        for section in sections:
            text = section.get_text()

            # Check if this is a category header
            if self._is_category_header(text):
                current_category = text.strip()
                if current_category not in required:
                    required[current_category] = []
                continue

            # Extract course codes from this section
            courses = course_pattern.findall(text)
            if courses and current_category in required:
                for dept, number in courses:
                    course_code = f"{dept} {number}"
                    if course_code not in required[current_category]:
                        required[current_category].append(course_code)

        return required

    def _is_category_header(self, text: str) -> bool:
        """Check if text is likely a category header"""
        text = text.strip()

        # Common requirement category keywords
        keywords = [
            'core', 'foundation', 'required', 'prerequisite', 'major',
            'concentration', 'area', 'elective', 'general education',
            'upper division', 'lower division', 'business core',
            'major requirements', 'program requirements'
        ]

        text_lower = text.lower()

        # Must be short enough to be a header
        if len(text) > 100:
            return False

        # Must contain a keyword
        if not any(keyword in text_lower for keyword in keywords):
            return False

        # Should not contain course codes (headers don't list courses)
        if re.search(r'\b[A-Z]{2,4}\s+\d{4}', text):
            return False

        return True

    def _extract_elective_groups(self, content) -> List[Dict]:
        """
        Extract elective groups with their requirements.

        Returns list of dicts with:
            - name: Group name
            - hours: Credit hours required
            - courses: List of course codes (if specified)
            - raw_text: Original text
        """
        elective_groups = []

        # Look for elective sections
        text = content.get_text()

        # Pattern for elective requirements
        # "Select X hours from: DEPT #### or DEPT ####"
        # "Choose Y courses from the following:"
        elective_pattern = re.compile(
            r'((?:select|choose)\s+\d+\s+(?:hours?|courses?)[^:]+:?.+?)(?=(?:select|choose|\n\n|$))',
            re.IGNORECASE | re.DOTALL
        )

        matches = elective_pattern.finditer(text)

        for match in matches:
            elective_text = match.group(1).strip()

            # Extract hours
            hours_match = re.search(r'(\d+)\s+(?:credit\s+)?hours?', elective_text, re.IGNORECASE)
            hours = int(hours_match.group(1)) if hours_match else 0

            # Extract course codes
            course_pattern = re.compile(r'\b([A-Z]{2,4})\s+(\d{4}[A-Z]?)\b')
            courses = [f"{dept} {num}" for dept, num in course_pattern.findall(elective_text)]

            # Determine group name (first line or sentence)
            name_match = re.match(r'([^:\n]+)', elective_text)
            name = name_match.group(1).strip() if name_match else "Electives"

            elective_groups.append({
                "name": name,
                "hours": hours,
                "courses": courses,
                "raw_text": elective_text[:200]  # Limit length
            })

        return elective_groups

    def _extract_progression_notes(self, text: str) -> str:
        """Extract progression or eligibility notes"""
        notes = []

        # Look for progression-related sections
        patterns = [
            r'Progression\s+Requirements?:(.+?)(?=\n\n|\Z)',
            r'Eligibility:(.+?)(?=\n\n|\Z)',
            r'Admission\s+to\s+(?:the\s+)?Major:(.+?)(?=\n\n|\Z)',
            r'Prerequisites\s+for\s+Major:(.+?)(?=\n\n|\Z)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                note_text = match.group(1).strip()
                # Clean up whitespace
                note_text = re.sub(r'\s+', ' ', note_text)
                notes.append(note_text)

        return " ".join(notes) if notes else ""

    def _extract_restrictions(self, text: str) -> str:
        """Extract enrollment restrictions or special requirements"""
        restrictions = []

        patterns = [
            r'Restrictions?:(.+?)(?=\n\n|\Z)',
            r'Special\s+Requirements?:(.+?)(?=\n\n|\Z)',
            r'Limited\s+Enrollment:(.+?)(?=\n\n|\Z)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                restriction_text = match.group(1).strip()
                restriction_text = re.sub(r'\s+', ' ', restriction_text)
                restrictions.append(restriction_text)

        return " ".join(restrictions) if restrictions else ""

    def scrape_major(self, major_name: str, poid: str = None) -> Optional[MajorRequirements]:
        """
        Scrape requirements for a single major.

        Args:
            major_name: Name of major
            poid: Optional program ID

        Returns:
            MajorRequirements object
        """
        print(f"\nScraping major requirements: {major_name}")

        major_data = self.parse_major_requirements(major_name, poid)

        if major_data:
            print(f"  ✓ Extracted {len(major_data.required_courses)} requirement categories")
            print(f"  ✓ Found {len(major_data.elective_groups)} elective groups")
            print(f"  ✓ Total hours: {major_data.total_hours}")

        return major_data

    def scrape_multiple_majors(self, major_list: List[str]) -> List[MajorRequirements]:
        """Scrape multiple majors"""
        results = []

        for major_name in major_list:
            major_data = self.scrape_major(major_name)
            if major_data:
                results.append(major_data)

        return results

    def save_to_json(self, majors: List[MajorRequirements], output_file: str):
        """Save parsed major requirements to JSON"""
        from datetime import datetime

        data = []
        for major in majors:
            major_dict = asdict(major)
            major_dict["parsed_date"] = datetime.now().isoformat()
            data.append(major_dict)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved {len(majors)} major(s) to {output_file}")


def main():
    """Example usage: Scrape CIS and Health Science Professions"""
    parser = GSUMajorRequirementsParser(catalog_id="42")

    # List of majors to scrape
    majors_to_scrape = [
        "Computer Information Systems",
        "Health Science Professions"
    ]

    print("=" * 70)
    print("SCRAPING MAJOR REQUIREMENTS FROM GSU CATALOG")
    print("=" * 70)

    results = parser.scrape_multiple_majors(majors_to_scrape)

    if results:
        # Save to JSON
        output_file = "data/major_requirements/major_requirements_2025_2026.json"
        parser.save_to_json(results, output_file)

        # Print summary
        print("\n" + "=" * 70)
        print("SCRAPING SUMMARY")
        print("=" * 70)

        for major_data in results:
            print(f"\n{major_data.major_name} ({major_data.degree_type})")
            print(f"  College: {major_data.college}")
            print(f"  Total Hours: {major_data.total_hours}")
            print(f"  Requirement Categories: {len(major_data.required_courses)}")
            for category, courses in major_data.required_courses.items():
                print(f"    - {category}: {len(courses)} courses")
            print(f"  Elective Groups: {len(major_data.elective_groups)}")


if __name__ == "__main__":
    main()

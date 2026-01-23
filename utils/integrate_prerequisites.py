"""
Integrate Parsed Prerequisites into Course Planner

This module integrates the raw prerequisite data parsed from GSU's catalog
into the existing course planner data structure used by CatalogLoader.

Usage:
    python utils/integrate_prerequisites.py

This will:
1. Load parsed prerequisite data from data/parsed_prerequisites/
2. Merge it with existing catalog JSON files
3. Update or create catalog files in data/course_catalogs/
"""

import json
import os
from typing import Dict, List
from pathlib import Path


class PrerequisiteIntegrator:
    """
    Integrates parsed prerequisite data into the existing catalog structure.
    """

    def __init__(self,
                 parsed_data_dir: str = "data/parsed_prerequisites",
                 catalog_dir: str = "data/course_catalogs"):
        """
        Initialize integrator.

        Args:
            parsed_data_dir: Directory with parsed prerequisite JSON files
            catalog_dir: Directory with existing catalog JSON files
        """
        self.parsed_data_dir = Path(parsed_data_dir)
        self.catalog_dir = Path(catalog_dir)

    def load_parsed_courses(self, filename: str) -> List[Dict]:
        """
        Load parsed course data from JSON file.

        Args:
            filename: Name of JSON file in parsed_data_dir

        Returns:
            List of parsed course dictionaries
        """
        filepath = self.parsed_data_dir / filename

        if not filepath.exists():
            print(f"Error: File not found: {filepath}")
            return []

        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def convert_to_catalog_format(self, parsed_courses: List[Dict],
                                    school: str = "Georgia State University",
                                    major: str = "Computer Science") -> Dict:
        """
        Convert parsed prerequisite data into catalog JSON format.

        This creates the structure expected by CatalogLoader:
        {
          "school": "...",
          "major": "...",
          "metadata": {...},
          "courses": {
            "CSC 1301": {
              "name": "...",
              "credits": 4,
              "prerequisites": [],  # Will be parsed from prerequisites_raw later
              "description": "...",
              "prerequisites_raw": "...",  # NEW: exact catalog text
              "corequisites_raw": "...",   # NEW: exact catalog text
              "restrictions_raw": "..."     # NEW: exact catalog text
            }
          }
        }

        Args:
            parsed_courses: List of parsed course data
            school: School name
            major: Major name

        Returns:
            Catalog dictionary in expected format
        """
        catalog = {
            "school": school,
            "major": major,
            "metadata": {
                "major": major,
                "degree_type": "BS",
                "university": school,
                "catalog_year": "2025-2026",
                "total_credits_required": 120,
                "description": f"Bachelor of Science in {major}",
                "source": "GSU Modern Campus Catalog - Parsed Prerequisites",
                "parsed_date": None  # Will be set when saved
            },
            "courses": {}
        }

        # Convert each parsed course
        for course in parsed_courses:
            course_code = course["course_code"]

            catalog["courses"][course_code] = {
                "name": course["title"],
                "credits": course["credits"],
                "description": course.get("description", ""),

                # Preserve RAW prerequisite text (exact from catalog)
                "prerequisites_raw": course.get("prerequisites_raw", ""),
                "corequisites_raw": course.get("corequisites_raw", ""),
                "restrictions_raw": course.get("restrictions_raw", ""),

                # Placeholder for parsed prerequisites (to be filled by logic later)
                # For now, keep empty lists - prerequisite interpretation is out of scope
                "prerequisites": [],
                "corequisites": [],

                # Minimum grade (if mentioned in prerequisite text)
                "min_grade": "C",  # Default, can be parsed from prerequisites_raw

                # Store original coid for reference
                "coid": course.get("coid", "")
            }

        return catalog

    def merge_with_existing_catalog(self, new_catalog: Dict, existing_file: str) -> Dict:
        """
        Merge new parsed data with existing catalog file.

        Args:
            new_catalog: New catalog dict with parsed data
            existing_file: Name of existing catalog file

        Returns:
            Merged catalog dictionary
        """
        filepath = self.catalog_dir / existing_file

        if not filepath.exists():
            print(f"No existing catalog found at {filepath}")
            print(f"Will create new catalog file")
            return new_catalog

        # Load existing catalog
        with open(filepath, 'r', encoding='utf-8') as f:
            existing = json.load(f)

        # Merge courses - new data overwrites old for matching course codes
        if "courses" not in existing:
            existing["courses"] = {}

        for course_code, course_data in new_catalog["courses"].items():
            if course_code in existing["courses"]:
                # Merge: keep existing data but update with new prerequisite fields
                existing["courses"][course_code].update({
                    "prerequisites_raw": course_data["prerequisites_raw"],
                    "corequisites_raw": course_data["corequisites_raw"],
                    "restrictions_raw": course_data["restrictions_raw"],
                    "coid": course_data.get("coid", "")
                })
                print(f"  Updated: {course_code}")
            else:
                # New course not in existing catalog
                existing["courses"][course_code] = course_data
                print(f"  Added: {course_code}")

        # Update metadata
        if "metadata" not in existing:
            existing["metadata"] = {}
        existing["metadata"]["source"] = "GSU Modern Campus Catalog - Parsed Prerequisites"

        return existing

    def save_catalog(self, catalog: Dict, output_file: str):
        """
        Save catalog to JSON file.

        Args:
            catalog: Catalog dictionary
            output_file: Output filename
        """
        from datetime import datetime

        # Update parsed date
        if "metadata" in catalog:
            catalog["metadata"]["parsed_date"] = datetime.now().isoformat()

        filepath = self.catalog_dir / output_file

        # Create directory if needed
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved catalog to: {filepath}")

    def integrate_csc_prerequisites(self, parsed_file: str = "csc_prerequisites_catalog_38.json"):
        """
        Integrate CSC prerequisites into the Computer Science catalog.

        Args:
            parsed_file: Name of parsed prerequisite JSON file
        """
        print("="*70)
        print("INTEGRATING CSC PREREQUISITES INTO CATALOG")
        print("="*70)

        # Load parsed data
        print(f"\n1. Loading parsed data from: {parsed_file}")
        parsed_courses = self.load_parsed_courses(parsed_file)

        if not parsed_courses:
            print("  ✗ No parsed courses found")
            return

        print(f"  ✓ Loaded {len(parsed_courses)} parsed courses")

        # Convert to catalog format
        print(f"\n2. Converting to catalog format...")
        catalog = self.convert_to_catalog_format(
            parsed_courses,
            school="Georgia State University",
            major="Computer Science"
        )
        print(f"  ✓ Converted {len(catalog['courses'])} courses")

        # Merge with existing catalog
        print(f"\n3. Merging with existing catalog...")
        existing_file = "cs_major.json"
        merged_catalog = self.merge_with_existing_catalog(catalog, existing_file)

        # Save
        print(f"\n4. Saving updated catalog...")
        self.save_catalog(merged_catalog, existing_file)

        print(f"\n{'='*70}")
        print("INTEGRATION COMPLETE")
        print(f"{'='*70}")
        print(f"\nCourses now have prerequisite information that can be queried:")
        print(f"  - prerequisites_raw: Exact text from catalog")
        print(f"  - corequisites_raw: Exact text from catalog")
        print(f"  - restrictions_raw: Exact text from catalog")
        print(f"\nNext steps:")
        print(f"  1. Use CatalogLoader to query prerequisite data")
        print(f"  2. Implement logic to parse prerequisites_raw into structured format")
        print(f"  3. Update course recommendation engine to use prerequisite data")


def main():
    """Example usage"""
    integrator = PrerequisiteIntegrator()

    # Integrate CSC courses from full scrape
    integrator.integrate_csc_prerequisites("csc_prerequisites_catalog_38.json")


if __name__ == "__main__":
    main()

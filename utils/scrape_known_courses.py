"""
Scrape prerequisites for known courses in cs_major.json

This script reads course codes from cs_major.json and attempts to find and scrape
their prerequisite data using Google search + direct parsing.
"""

import json
from pathlib import Path
from gsu_prerequisite_parser import GSUPrerequisiteParser
import time

def load_course_codes(catalog_file: str = "data/course_catalogs/cs_major.json"):
    """Load all course codes from existing catalog"""
    with open(catalog_file, 'r') as f:
        catalog = json.load(f)

    # Get all CSC and MATH course codes
    course_codes = [code for code in catalog.get("courses", {}).keys()
                   if code.startswith("CSC") or code.startswith("MATH")]

    return sorted(course_codes)

def search_course_coid(parser, course_code: str):
    """
    Search GSU catalog for course and return coid.

    Uses Google search: site:catalogs.gsu.edu "CSC 1301"
    Then extracts coid from the result URL.
    """
    import requests
    from bs4 import BeautifulSoup
    import re

    # If we already know some coids, use them
    known_coids = {
        "CSC 1301": "88199",
        "CSC 1302": "88200",
        "CSC 2720": "88202",
    }

    if course_code in known_coids:
        return known_coids[course_code]

    # For others, we'll need to search or increment from known values
    # GSU coids appear to be sequential, so we can try nearby numbers
    return None

def main():
    print("="*70)
    print("SCRAPING PREREQUISITES FOR KNOWN COURSES")
    print("="*70)

    # Load course codes from catalog
    course_codes = load_course_codes()
    print(f"\nFound {len(course_codes)} courses in catalog")
    print(f"Courses: {', '.join(course_codes[:10])}...")

    # Initialize parser
    parser = GSUPrerequisiteParser(catalog_id="38")

    # For now, let's just scrape the courses we have coids for
    # and see if we can find patterns for others

    known_courses = [
        ("88199", "CSC 1301"),
        ("88200", "CSC 1302"),
        ("88202", "CSC 2720"),
    ]

    # Let's try some sequential coids for other core CSC courses
    # CSC 3210, CSC 3320, CSC 3350, CSC 4320, CSC 4330, CSC 4520
    # We can try coids in the 88200-88250 range

    print("\n" + "="*70)
    print("Attempting to scrape courses with known/guessed coids")
    print("="*70)

    results = []

    # Scrape known courses
    for coid, course_code in known_courses:
        print(f"\nScraping {course_code} (coid={coid})...")
        course = parser.parse_course_detail(coid, course_code)
        if course:
            results.append(course)
            print(f"  ✓ Success")
        else:
            print(f"  ✗ Failed")

    # Try sequential coids for other CSC courses (educated guess)
    # This is a bit hacky but might work
    print("\n" + "="*70)
    print("Attempting to find additional CSC courses by trying sequential coids")
    print("="*70)

    for coid in range(88201, 88230):
        if str(coid) in ["88202"]:  # Skip ones we already tried
            continue

        print(f"\nTrying coid={coid}...")
        course = parser.parse_course_detail(str(coid))

        if course and course.course_code.startswith("CSC"):
            results.append(course)
            print(f"  ✓ Found {course.course_code}!")
        elif course:
            print(f"  Found {course.course_code} (not CSC)")
        else:
            print(f"  No course found")

        # Rate limit
        time.sleep(1)

    # Save results
    if results:
        print("\n" + "="*70)
        print(f"Successfully scraped {len(results)} courses")
        print("="*70)

        output_file = "data/parsed_prerequisites/csc_prerequisites_catalog_38.json"
        parser.save_to_json(results, output_file)

        # Show what we got
        print("\nScraped courses:")
        for course in results:
            prereq = f" - Prereq: {course.prerequisites_raw}" if course.prerequisites_raw else ""
            print(f"  {course.course_code}: {course.title}{prereq}")
    else:
        print("\n✗ No courses were successfully scraped")

if __name__ == "__main__":
    main()

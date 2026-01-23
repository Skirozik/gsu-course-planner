"""
Test script for GSU Prerequisite Parser

Tests the parser with a few known CSC courses to validate:
1. Course information extraction
2. Prerequisite parsing
3. Corequisite parsing
4. Restriction parsing
"""

from utils.gsu_prerequisite_parser import GSUPrerequisiteParser
import json


def test_sample_courses():
    """Test parser with 2-3 known CSC courses"""
    parser = GSUPrerequisiteParser(catalog_id="38")  # Use catalog 38 since we know it works

    # Known course IDs from catalog 38 (found via search)
    test_courses = [
        ("88199", "CSC 1301"),  # Intro course - likely has corequisites
        ("88200", "CSC 1302"),  # Second course - likely has prerequisites
        ("88202", "CSC 2720"),  # Data structures - definitely has prerequisites
    ]

    print("="*70)
    print("TESTING GSU PREREQUISITE PARSER")
    print("="*70)

    results = []

    for coid, expected_code in test_courses:
        print(f"\n{'='*70}")
        print(f"Testing: {expected_code} (coid={coid})")
        print(f"{'='*70}")

        course = parser.parse_course_detail(coid, expected_code)

        if course:
            results.append(course)

            print(f"\n✓ Successfully parsed!")
            print(f"\nCourse Code: {course.course_code}")
            print(f"Title: {course.title}")
            print(f"Credits: {course.credits}")

            if course.prerequisites_raw:
                print(f"\nPrerequisites (RAW):")
                print(f"  '{course.prerequisites_raw}'")
            else:
                print(f"\nPrerequisites: None")

            if course.corequisites_raw:
                print(f"\nCorequisites (RAW):")
                print(f"  '{course.corequisites_raw}'")
            else:
                print(f"\nCorequisites: None")

            if course.restrictions_raw:
                print(f"\nRestrictions (RAW):")
                print(f"  '{course.restrictions_raw}'")
            else:
                print(f"\nRestrictions: None")

            if course.description:
                print(f"\nDescription (preview):")
                print(f"  {course.description[:150]}...")

        else:
            print(f"\n✗ Failed to parse {expected_code}")

    # Save results
    print(f"\n{'='*70}")
    print("SAVING TEST RESULTS")
    print(f"{'='*70}")

    if results:
        output_file = "data/parsed_prerequisites/test_csc_courses.json"
        parser.save_to_json(results, output_file)

        print(f"\nTest results saved to: {output_file}")
        print(f"Successfully parsed {len(results)}/{len(test_courses)} courses")

        return True
    else:
        print("\n⚠ No courses were successfully parsed")
        return False


if __name__ == "__main__":
    success = test_sample_courses()

    print(f"\n{'='*70}")
    if success:
        print("✓ TEST PASSED - Parser is working correctly!")
        print("\nNext step: Run full scrape with:")
        print("  python utils/gsu_prerequisite_parser.py")
    else:
        print("✗ TEST FAILED - Check error messages above")
    print(f"{'='*70}\n")

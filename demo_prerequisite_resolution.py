"""
Demo: Enhanced Prerequisite Resolution

Demonstrates the prerequisite resolution layer using real GSU catalog data
with student transcripts including grades.
"""

from utils.catalog_loader import get_catalog_loader
from utils.prerequisite_resolver import get_prerequisite_resolver


def demo_basic_eligibility():
    """Demo: Check eligibility for a course with grade requirements"""
    print("=" * 70)
    print("DEMO 1: Basic Eligibility Check with Grades")
    print("=" * 70)

    catalog = get_catalog_loader()

    # Scenario: Student wants to take CSC 4320 (Operating Systems)
    # Prerequisites: CSC 3320 with grade of C or higher

    print("\nCourse: CSC 4320 - Operating Systems")
    print("Prerequisites: CSC 3320 with grade of C or higher\n")

    # Student A: Has CSC 3320 with B
    completed_a = [
        {"course_code": "CSC 3320", "grade": "B"}
    ]
    result_a = catalog.check_prerequisites_with_grades(
        "Georgia State University",
        "Computer Science",
        "CSC 4320",
        completed_a
    )
    print("Student A (CSC 3320 with B):")
    print(f"  ✅ Eligible: {result_a['eligible']}")
    print(f"  Reason: {result_a['reason']}\n")

    # Student B: Has CSC 3320 with D
    completed_b = [
        {"course_code": "CSC 3320", "grade": "D"}
    ]
    result_b = catalog.check_prerequisites_with_grades(
        "Georgia State University",
        "Computer Science",
        "CSC 4320",
        completed_b
    )
    print("Student B (CSC 3320 with D):")
    print(f"  ❌ Eligible: {result_b['eligible']}")
    print(f"  Reason: {result_b['reason']}\n")

    # Student C: Hasn't taken CSC 3320
    completed_c = []
    result_c = catalog.check_prerequisites_with_grades(
        "Georgia State University",
        "Computer Science",
        "CSC 4320",
        completed_c
    )
    print("Student C (hasn't taken CSC 3320):")
    print(f"  ❌ Eligible: {result_c['eligible']}")
    print(f"  Reason: {result_c['reason']}\n")


def demo_complex_prerequisites():
    """Demo: Complex prerequisite with OR logic"""
    print("=" * 70)
    print("DEMO 2: Complex Prerequisites with OR Logic")
    print("=" * 70)

    catalog = get_catalog_loader()

    # Scenario: Student wants to take CSC 4520 (Design and Analysis of Algorithms)
    # Prerequisites: (CSC 2720 or DSCI 2720) and either MATH 3020 or MATH 3030

    print("\nCourse: CSC 4520 - Design and Analysis of Algorithms")
    print("Prerequisites: (CSC 2720 or DSCI 2720) and MATH 2420 with C or higher\n")

    # Student A: Has both CSC 2720 and MATH 2420
    completed_a = [
        {"course_code": "CSC 2720", "grade": "B"},
        {"course_code": "MATH 2420", "grade": "A"}
    ]
    result_a = catalog.check_prerequisites_with_grades(
        "Georgia State University",
        "Computer Science",
        "CSC 4520",
        completed_a
    )
    print("Student A (CSC 2720: B, MATH 2420: A):")
    print(f"  ✅ Eligible: {result_a['eligible']}")
    print(f"  Reason: {result_a['reason']}\n")

    # Student B: Has CSC 2720 but missing MATH 2420
    completed_b = [
        {"course_code": "CSC 2720", "grade": "A"}
    ]
    result_b = catalog.check_prerequisites_with_grades(
        "Georgia State University",
        "Computer Science",
        "CSC 4520",
        completed_b
    )
    print("Student B (CSC 2720: A, no math):")
    print(f"  ❌ Eligible: {result_b['eligible']}")
    print(f"  Reason: {result_b['reason']}\n")


def demo_all_eligible_courses():
    """Demo: Get all courses a student can take"""
    print("=" * 70)
    print("DEMO 3: All Eligible Courses for a Student")
    print("=" * 70)

    catalog = get_catalog_loader()

    # Student transcript
    completed = [
        {"course_code": "CSC 1301", "grade": "B"},
        {"course_code": "CSC 1302", "grade": "A"},
        {"course_code": "CSC 2720", "grade": "B"},
        {"course_code": "MATH 1111", "grade": "A"},
        {"course_code": "MATH 1113", "grade": "B"},
        {"course_code": "MATH 2211", "grade": "C"},
        {"course_code": "MATH 2420", "grade": "B"}
    ]

    print("\nStudent Transcript:")
    for course in completed:
        print(f"  {course['course_code']}: {course['grade']}")

    # Currently enrolled
    in_progress = ["CSC 3210"]
    print(f"\nCurrently Enrolled: {', '.join(in_progress)}")

    # Get eligible courses
    eligible = catalog.get_eligible_courses_with_grades(
        "Georgia State University",
        "Computer Science",
        completed,
        in_progress,
        limit=10
    )

    print(f"\n📚 Courses You Can Take Now ({len(eligible)} total):\n")
    for course in eligible[:10]:
        print(f"  ✅ {course['course_code']}: {course['course_name']}")
        if course.get('eligibility_reason'):
            print(f"     Reason: {course['eligibility_reason']}")


def demo_prerequisite_parsing():
    """Demo: Show how prerequisites are parsed"""
    print("=" * 70)
    print("DEMO 4: Prerequisite Parsing Examples")
    print("=" * 70)

    resolver = get_prerequisite_resolver()

    examples = [
        "CSC 1301 with a C or higher",
        "(CSC 2720 or DSCI 2720) and either MATH 3020 or MATH 3030 with a C or higher",
        "CSC 2720, CSC 3210, and CSC 3320 with a C or higher",
        "CSC 3320 with grade of C or higher. Students must meet the Computer Science Major Eligibility",
        "MATH 2215 with grade of C or higher and the ability to program in a high-level language"
    ]

    for prereq_text in examples:
        print(f"\nRaw Text:")
        print(f"  {prereq_text}")

        groups = resolver.parse_prerequisites(prereq_text)
        print(f"Parsed Groups:")
        for group in groups:
            print(f"  {group}")


def main():
    print("\n" + "=" * 70)
    print("PREREQUISITE RESOLUTION DEMONSTRATION")
    print("Using Real GSU Course Catalog Data")
    print("=" * 70 + "\n")

    demo_basic_eligibility()
    print("\n")

    demo_complex_prerequisites()
    print("\n")

    demo_all_eligible_courses()
    print("\n")

    demo_prerequisite_parsing()

    print("\n" + "=" * 70)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

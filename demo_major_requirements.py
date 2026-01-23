"""
Demo: Major Requirements System

Demonstrates the major requirements loading and integration system.
"""

from utils.major_requirements_loader import get_major_requirements_loader


def demo_load_majors():
    """Demo: Load and display available majors"""
    print("=" * 70)
    print("DEMO 1: Loading Major Requirements")
    print("=" * 70)

    loader = get_major_requirements_loader()
    majors = loader.get_all_majors()

    print(f"\nLoaded {len(majors)} major(s):\n")

    for major_name in majors:
        metadata = loader.get_major_metadata(major_name)
        print(f"  • {major_name}")
        print(f"    Degree: {metadata['degree_type']}")
        print(f"    College: {metadata['college']}")
        print(f"    Total Hours: {metadata['total_hours']}\n")


def demo_major_structure():
    """Demo: Show major requirement structure"""
    print("=" * 70)
    print("DEMO 2: Major Requirement Structure")
    print("=" * 70)

    loader = get_major_requirements_loader()

    # Example: Computer Information Systems
    major_name = "Computer Information Systems"
    print(f"\nMajor: {major_name}\n")

    # Get requirements by category
    requirements = loader.get_requirements_by_category(major_name)

    print("Required Courses by Category:")
    for category, courses in requirements.items():
        if courses:  # Only show categories with courses
            print(f"\n  {category} ({len(courses)} courses):")
            for course in courses[:5]:  # Show first 5
                print(f"    - {course}")
            if len(courses) > 5:
                print(f"    ... and {len(courses) - 5} more")

    # Get elective groups
    electives = loader.get_elective_groups(major_name)
    print(f"\n  Elective Groups ({len(electives)}):")
    for group in electives:
        print(f"\n    {group['name']}:")
        print(f"      Required Hours: {group['hours']}")
        if group['courses']:
            print(f"      Options: {', '.join(group['courses'][:5])}...")


def demo_progress_tracking():
    """Demo: Track student progress toward major"""
    print("\n" + "=" * 70)
    print("DEMO 3: Student Progress Tracking")
    print("=" * 70)

    loader = get_major_requirements_loader()

    # Example student transcript
    completed_courses = [
        "CSC 1301", "CSC 1302",  # CS courses
        "ACCT 2101", "ACCT 2102",  # Accounting
        "ECON 2105", "ECON 2106",  # Economics
        "BUSA 2100",  # Business Statistics
        "CIS 2200"  # Intro to CIS
    ]

    print(f"\nStudent has completed {len(completed_courses)} courses:")
    print(f"  {', '.join(completed_courses)}")

    # Check progress for CIS major
    major_name = "Computer Information Systems"
    progress = loader.check_major_progress(major_name, completed_courses)

    print(f"\nProgress toward {major_name}:")
    print(f"  Overall: {progress['total_completed_courses']}/{progress['total_required_courses']} courses ({progress['overall_progress_percentage']}%)")

    print(f"\n  By Category:")
    for category, cat_progress in progress['category_progress'].items():
        if cat_progress['total'] > 0:
            print(f"    {category}: {cat_progress['completed']}/{cat_progress['total']} ({cat_progress['percentage']}%)")


def demo_next_courses():
    """Demo: Get next required courses"""
    print("\n" + "=" * 70)
    print("DEMO 4: Next Required Courses")
    print("=" * 70)

    loader = get_major_requirements_loader()

    # Same student from previous demo
    completed_courses = [
        "CSC 1301", "CSC 1302",
        "ACCT 2101", "ACCT 2102",
        "ECON 2105", "ECON 2106",
        "BUSA 2100", "CIS 2200"
    ]

    # Currently enrolled
    in_progress = ["BUSA 3000", "CIS 3300"]

    major_name = "Computer Information Systems"

    print(f"\nStudent is currently taking: {', '.join(in_progress)}")

    next_courses = loader.get_next_required_courses(
        major_name,
        completed_courses,
        in_progress
    )

    print(f"\nNext Required Courses for {major_name}:\n")

    for category, courses in next_courses.items():
        if courses:
            print(f"  {category}:")
            for course in courses[:5]:  # Show first 5
                print(f"    - {course}")
            if len(courses) > 5:
                print(f"    ... and {len(courses) - 5} more")


def demo_health_science():
    """Demo: Show Health Science Professions major"""
    print("\n" + "=" * 70)
    print("DEMO 5: Health Science Professions Major")
    print("=" * 70)

    loader = get_major_requirements_loader()

    major_name = "Health Sciences"
    metadata = loader.get_major_metadata(major_name)

    print(f"\nMajor: {metadata['major_name']}")
    print(f"Degree: {metadata['degree_type']}")
    print(f"College: {metadata['college']}")
    print(f"Total Hours: {metadata['total_hours']}")

    if metadata['progression_notes']:
        print(f"\nProgression Requirements:")
        print(f"  {metadata['progression_notes']}")

    if metadata['restrictions']:
        print(f"\nEnrollment Restrictions:")
        print(f"  {metadata['restrictions']}")

    # Show core courses
    requirements = loader.get_requirements_by_category(major_name)
    print(f"\nCore Health Science Courses:")
    if 'Core Health Science Courses' in requirements:
        for course in requirements['Core Health Science Courses']:
            print(f"  - {course}")


def main():
    print("\n" + "=" * 70)
    print("MAJOR REQUIREMENTS SYSTEM DEMONSTRATION")
    print("=" * 70 + "\n")

    demo_load_majors()
    demo_major_structure()
    demo_progress_tracking()
    demo_next_courses()
    demo_health_science()

    print("\n" + "=" * 70)
    print("✅ DEMONSTRATION COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

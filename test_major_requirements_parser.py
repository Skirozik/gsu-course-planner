"""
Test Major Requirements Parser

Creates example major requirements data to demonstrate the structure
and integration with existing catalog system.
"""

from utils.gsu_major_requirements_parser import MajorRequirements
import json
from datetime import datetime
from pathlib import Path


def create_cis_example() -> MajorRequirements:
    """
    Create example parsed data for Computer Information Systems major.

    This represents what would be extracted from the catalog page.
    """
    return MajorRequirements(
        major_name="Computer Information Systems",
        degree_type="B.S.",
        college="Robinson College of Business",
        catalog_year="2025-2026",
        total_hours=120,
        required_courses={
            "Business Core": [
                "ACCT 2101",  # Principles of Accounting I
                "ACCT 2102",  # Principles of Accounting II
                "ECON 2105",  # Principles of Macroeconomics
                "ECON 2106",  # Principles of Microeconomics
                "BUSA 2100",  # Business Statistics
                "BUSA 3000",  # International Business
                "FI 3300",    # Business Finance
                "MGT 3400",   # Management
                "MK 3400",    # Marketing
                "BUSA 4850",  # Strategic Management
            ],
            "CIS Core Requirements": [
                "CSC 1301",   # Principles of Computer Science I
                "CSC 1302",   # Principles of Computer Science II
                "CIS 2200",   # Introduction to Computer Information Systems
                "CIS 3300",   # Database Management Systems
                "CIS 3400",   # Systems Analysis and Design
                "CIS 3500",   # Enterprise Architecture
                "CIS 4200",   # Information Security
                "CIS 4400",   # IT Project Management
                "CIS 4500",   # Business Intelligence and Analytics
            ],
            "Major Electives": [
                # Would list specific courses or allow choice
            ],
            "General Education": [
                # Would list core curriculum requirements
            ]
        },
        elective_groups=[
            {
                "name": "CIS Upper Division Electives",
                "hours": 9,
                "courses": [
                    "CIS 4100", "CIS 4250", "CIS 4300",
                    "CIS 4350", "CIS 4600", "CIS 4700"
                ],
                "raw_text": "Select 9 hours from the following CIS electives"
            },
            {
                "name": "Business Electives",
                "hours": 6,
                "courses": [],  # Any business course
                "raw_text": "Select 6 hours of business electives at 3000-level or above"
            }
        ],
        progression_notes="Students must maintain a 2.5 GPA in major courses. Completion of MATH 1111 or higher required before enrolling in business core courses.",
        restrictions="Enrollment in upper-division CIS courses requires admission to the Robinson College of Business and completion of all lower-division business and CIS prerequisites.",
        source_url="https://catalogs.gsu.edu/content.php?catoid=42&navoid=XXXXX",
        parsed_date=datetime.now().isoformat()
    )


def create_health_science_example() -> MajorRequirements:
    """
    Create example parsed data for Health Science Professions major.

    This represents what would be extracted from the catalog page.
    """
    return MajorRequirements(
        major_name="Health Science Professions",
        degree_type="B.S.",
        college="Byrdine F. Lewis College of Nursing and Health Professions",
        catalog_year="2025-2026",
        total_hours=120,
        required_courses={
            "Core Health Science Courses": [
                "HSC 2110",   # Introduction to Health Science Professions
                "HSC 2210",   # Medical Terminology
                "BIOL 2107",  # Principles of Biology I
                "BIOL 2108",  # Principles of Biology II
                "CHEM 1151",  # Survey of Chemistry I
                "CHEM 1152",  # Survey of Chemistry II
                "MATH 1111",  # College Algebra
                "STAT 1401",  # Elementary Statistics
            ],
            "Professional Development": [
                "HSC 3100",   # Healthcare Systems and Policy
                "HSC 3200",   # Health Informatics
                "HSC 4100",   # Research Methods in Health Sciences
                "HSC 4500",   # Healthcare Ethics and Law
                "HSC 4900",   # Senior Capstone in Health Sciences
            ],
            "Clinical Practice": [
                "HSC 4700",   # Clinical Practicum I
                "HSC 4800",   # Clinical Practicum II
            ],
            "General Education": [
                # Core curriculum requirements
            ]
        },
        elective_groups=[
            {
                "name": "Health Science Electives",
                "hours": 18,
                "courses": [
                    "HSC 3300", "HSC 3400", "HSC 3500",
                    "HSC 4200", "HSC 4300", "HSC 4600",
                    "NURS 3100", "NURS 3200"
                ],
                "raw_text": "Select 18 hours from health science or nursing electives in consultation with advisor"
            },
            {
                "name": "Science Electives",
                "hours": 6,
                "courses": [
                    "BIOL 3100", "BIOL 3200", "CHEM 2100", "PHYS 1111"
                ],
                "raw_text": "Select 6 hours from approved science electives"
            }
        ],
        progression_notes="Students must maintain a 2.75 GPA in major courses. Background check and immunizations required before clinical practicums. CPR certification required.",
        restrictions="Admission to clinical practicums requires completion of all prerequisite courses with grades of C or better, program admission, and health clearance documentation.",
        source_url="https://catalogs.gsu.edu/content.php?catoid=42&navoid=5400",
        parsed_date=datetime.now().isoformat()
    )


def save_example_data():
    """Save example major requirements data to JSON"""
    output_dir = Path("data/major_requirements")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create example data
    cis_major = create_cis_example()
    health_major = create_health_science_example()

    majors = [cis_major, health_major]

    # Convert to dict format
    data = []
    for major in majors:
        from dataclasses import asdict
        major_dict = asdict(major)
        data.append(major_dict)

    # Save to JSON
    output_file = output_dir / "major_requirements_2025_2026.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print("=" * 70)
    print("EXAMPLE MAJOR REQUIREMENTS DATA CREATED")
    print("=" * 70)
    print(f"\nSaved to: {output_file}\n")

    # Print summary
    for major_data in majors:
        print(f"\n{major_data.major_name} ({major_data.degree_type})")
        print(f"  College: {major_data.college}")
        print(f"  Total Hours: {major_data.total_hours}")
        print(f"  Requirement Categories: {len(major_data.required_courses)}")
        for category, courses in major_data.required_courses.items():
            if courses:  # Only show categories with courses
                print(f"    - {category}: {len(courses)} courses")
                print(f"      {', '.join(courses[:5])}{'...' if len(courses) > 5 else ''}")
        print(f"  Elective Groups: {len(major_data.elective_groups)}")
        for group in major_data.elective_groups:
            print(f"    - {group['name']}: {group['hours']} hours")
        if major_data.progression_notes:
            print(f"  Progression Notes: {major_data.progression_notes[:100]}...")

    print("\n" + "=" * 70)
    print("Note: This is example/template data.")
    print("Run the actual parser once correct navoid values are identified.")
    print("=" * 70)


if __name__ == "__main__":
    save_example_data()

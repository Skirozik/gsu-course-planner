"""
Test Section Ranking System

Tests the professor ranking and section recommendation system
"""

from utils.section_recommender import (
    get_ranked_sections,
    format_sections_display,
    get_best_section,
    get_fallback_sections
)
from utils.professor_ranking import ProfessorNormalizer


def test_name_normalization():
    """Test professor name normalization"""
    print("\n" + "=" * 60)
    print("TEST 1: Name Normalization")
    print("=" * 60)

    test_names = [
        "Smith, John",
        "Dr. John Smith",
        "Prof. Angela Lee",
        "Mary Johnson, PhD",
        "TBA",
        "Staff",
        "Robert Davis Jr."
    ]

    for raw_name in test_names:
        identity = ProfessorNormalizer.create_identity(raw_name)
        print(f"\nRaw: '{raw_name}'")
        print(f"  → Normalized: {identity.primary_name}")
        print(f"  → ID: {identity.professor_id}")
        print(f"  → Aliases: {identity.aliases[:3]}")  # Show first 3 aliases


def test_section_ranking():
    """Test section ranking with sample data"""
    print("\n" + "=" * 60)
    print("TEST 2: Section Ranking")
    print("=" * 60)

    # Sample sections for CSC 3320
    sections = [
        {
            "section": "001",
            "instructor": "John Smith",
            "crn": "12345",
            "time": "MWF 10:00-10:50",
            "days": "MWF",
            "location": "Classroom South 101"
        },
        {
            "section": "002",
            "instructor": "Angela Lee",
            "crn": "12346",
            "time": "TTh 2:00-3:15",
            "days": "TTh",
            "location": "Langdale Hall 200"
        },
        {
            "section": "003",
            "instructor": "Mary Johnson",
            "crn": "12347",
            "time": "MW 6:00-7:15",
            "days": "MW",
            "location": "Online"
        },
        {
            "section": "004",
            "instructor": "Staff",
            "crn": "12348",
            "time": "TTh 10:00-11:15",
            "days": "TTh",
            "location": "Library 305"
        }
    ]

    print(f"\nRanking sections for CSC 3320...")
    print(f"Number of sections: {len(sections)}")

    try:
        ranked = get_ranked_sections(
            course_code="CSC 3320",
            sections_data=sections,
            school="Georgia State University"
        )

        print(format_sections_display("CSC 3320", ranked))

        # Show ranking summary
        print("\n" + "=" * 60)
        print("RANKING SUMMARY:")
        print("=" * 60)
        for section in ranked:
            has_rmp = "✅" if section.rating else "❌"
            print(f"Rank {section.rank}: Section {section.section} - "
                  f"{section.instructor_normalized} (Score: {section.score}) {has_rmp}")

    except Exception as e:
        print(f"❌ Error during ranking: {e}")
        import traceback
        traceback.print_exc()


def test_best_section():
    """Test getting best section"""
    print("\n" + "=" * 60)
    print("TEST 3: Get Best Section")
    print("=" * 60)

    sections = [
        {"section": "001", "instructor": "Smith, John"},
        {"section": "002", "instructor": "Lee, Angela"},
        {"section": "003", "instructor": "TBA"}
    ]

    try:
        best = get_best_section("CSC 4520", sections)

        if best:
            print(f"\n🥇 BEST SECTION:")
            print(f"   Section: {best.section}")
            print(f"   Professor: {best.instructor_normalized}")
            print(f"   Rating: {best.rating or 'N/A'}")
            print(f"   Score: {best.score}")
        else:
            print("❌ No sections found")

    except Exception as e:
        print(f"❌ Error getting best section: {e}")


def test_fallback_sections():
    """Test getting fallback sections"""
    print("\n" + "=" * 60)
    print("TEST 4: Get Fallback Sections (Top 3)")
    print("=" * 60)

    sections = [
        {"section": "001", "instructor": "Professor A"},
        {"section": "002", "instructor": "Professor B"},
        {"section": "003", "instructor": "Professor C"},
        {"section": "004", "instructor": "Professor D"},
        {"section": "005", "instructor": "TBA"}
    ]

    try:
        top_3 = get_fallback_sections("MATH 2420", sections, top_n=3)

        print(f"\n📋 TOP 3 FALLBACK OPTIONS:")
        for i, section in enumerate(top_3, 1):
            print(f"\n{i}. Section {section.section} - {section.instructor_normalized}")
            print(f"   Score: {section.score}")
            if section.rating:
                print(f"   Rating: {section.rating}/5.0")

    except Exception as e:
        print(f"❌ Error getting fallback sections: {e}")


def test_multiple_courses():
    """Test ranking sections for multiple courses"""
    print("\n" + "=" * 60)
    print("TEST 5: Multiple Courses")
    print("=" * 60)

    from utils.section_recommender import get_ranked_sections_for_courses

    courses = {
        "CSC 3320": [
            {"section": "001", "instructor": "John Smith"},
            {"section": "002", "instructor": "Angela Lee"}
        ],
        "CSC 4520": [
            {"section": "001", "instructor": "Mary Johnson"},
            {"section": "002", "instructor": "TBA"}
        ]
    }

    try:
        results = get_ranked_sections_for_courses(courses)

        for course_code, ranked_sections in results.items():
            print(f"\n{course_code}: {len(ranked_sections)} sections")
            for section in ranked_sections:
                print(f"  Rank {section.rank}: {section.section} - "
                      f"{section.instructor_normalized} (Score: {section.score})")

    except Exception as e:
        print(f"❌ Error ranking multiple courses: {e}")


if __name__ == "__main__":
    print("\n🧪 SECTION RANKING SYSTEM TESTS")
    print("=" * 60)

    # Run all tests
    test_name_normalization()
    test_section_ranking()
    test_best_section()
    test_fallback_sections()
    test_multiple_courses()

    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 60)

"""
Section Recommender - Integrates RMP rankings with course scheduling

This module ties together:
  1. Professor name normalization
  2. RMP data fetching
  3. Section ranking by professor quality

Primary function: get_ranked_sections()
  - Takes course code and list of instructors
  - Returns sections sorted by professor quality
  - Best-rated professor first, TBA professors last
"""

from typing import Dict, List, Optional
from utils.rmp_integration import get_rmp_api
from utils.professor_ranking import (
    ProfessorNormalizer,
    SectionRanking,
    SectionRanker,
    create_ranked_sections,
    format_ranking_display
)
import logging

logger = logging.getLogger(__name__)


def get_ranked_sections(course_code: str,
                       sections_data: List[Dict],
                       school: str = "Georgia State University",
                       term: str = "Spring 2026") -> List[SectionRanking]:
    """
    Get sections for a course ranked by professor quality

    Args:
        course_code: Course code (e.g., "CSC 3320")
        sections_data: List of section info dicts
            [{
                "section": "001",
                "instructor": "Smith, John",
                "crn": "12345",
                "time": "MWF 10:00-10:50",
                "days": "MWF",
                "location": "Room 123"
            }, ...]
        school: School name for RMP lookup
        term: Semester term

    Returns:
        List of SectionRanking objects sorted by quality (best first)
    """
    # Extract unique instructor names
    instructor_names = []
    for section in sections_data:
        instructor = section.get("instructor", "")
        if instructor and instructor not in instructor_names:
            instructor_names.append(instructor)

    # Fetch RMP data for all instructors
    rmp_api = get_rmp_api()
    rmp_data_map = rmp_api.batch_search_professors(instructor_names)

    # Also try normalized names
    for raw_name in instructor_names:
        identity = ProfessorNormalizer.create_identity(raw_name)
        if identity.primary_name not in rmp_data_map:
            # Try looking up normalized name
            rmp_result = rmp_api.get_professor_rating(identity.primary_name, school)
            if rmp_result:
                rmp_data_map[identity.primary_name] = rmp_result

    # Create and rank sections
    ranked_sections = create_ranked_sections(
        course_code=course_code,
        sections_data=sections_data,
        rmp_data_map=rmp_data_map,
        term=term
    )

    logger.info(f"Ranked {len(ranked_sections)} sections for {course_code}")

    return ranked_sections


def get_ranked_sections_for_courses(courses_with_sections: Dict[str, List[Dict]],
                                   school: str = "Georgia State University",
                                   term: str = "Spring 2026") -> Dict[str, List[SectionRanking]]:
    """
    Get ranked sections for multiple courses at once

    Args:
        courses_with_sections: Dict mapping course codes to section data
            {
                "CSC 3320": [
                    {"section": "001", "instructor": "Smith, John", ...},
                    {"section": "002", "instructor": "Lee, Angela", ...}
                ],
                "CSC 4520": [...]
            }
        school: School name for RMP lookup
        term: Semester term

    Returns:
        Dict mapping course codes to ranked sections
    """
    results = {}

    for course_code, sections_data in courses_with_sections.items():
        try:
            ranked = get_ranked_sections(
                course_code=course_code,
                sections_data=sections_data,
                school=school,
                term=term
            )
            results[course_code] = ranked
        except Exception as e:
            logger.error(f"Error ranking sections for {course_code}: {e}")
            # Return unranked sections as fallback
            unranked = [
                SectionRanking(
                    course_code=course_code,
                    section=s.get("section", ""),
                    instructor_raw=s.get("instructor", "TBA"),
                    term=term
                )
                for s in sections_data
            ]
            results[course_code] = unranked

    return results


def format_sections_display(course_code: str, sections: List[SectionRanking]) -> str:
    """
    Format ranked sections for display

    Args:
        course_code: Course code
        sections: Ranked sections

    Returns:
        Formatted string
    """
    lines = [f"\n{course_code} - Sections Ranked by Professor Quality:\n"]
    lines.append("=" * 60)

    for section in sections:
        lines.append("\n" + format_ranking_display(section))
        lines.append("-" * 60)

    return "\n".join(lines)


def get_best_section(course_code: str,
                    sections_data: List[Dict],
                    school: str = "Georgia State University") -> Optional[SectionRanking]:
    """
    Get the single best section for a course (highest ranked professor)

    Args:
        course_code: Course code
        sections_data: List of section info dicts
        school: School name

    Returns:
        Best SectionRanking or None if no sections
    """
    ranked = get_ranked_sections(course_code, sections_data, school)

    if not ranked:
        return None

    return ranked[0]  # First is best


def get_fallback_sections(course_code: str,
                         sections_data: List[Dict],
                         school: str = "Georgia State University",
                         top_n: int = 3) -> List[SectionRanking]:
    """
    Get top N sections as fallback options (in case first choice fills up)

    Args:
        course_code: Course code
        sections_data: List of section info dicts
        school: School name
        top_n: Number of fallback options to return

    Returns:
        List of top N sections
    """
    ranked = get_ranked_sections(course_code, sections_data, school)

    return ranked[:top_n]


# Example usage for testing
if __name__ == "__main__":
    # Example: CSC 3320 with multiple sections
    example_sections = [
        {
            "section": "001",
            "instructor": "Smith, John",
            "crn": "12345",
            "time": "MWF 10:00-10:50",
            "days": "MWF",
            "location": "Classroom South 101"
        },
        {
            "section": "002",
            "instructor": "Lee, Angela",
            "crn": "12346",
            "time": "TTh 2:00-3:15",
            "days": "TTh",
            "location": "Langdale Hall 200"
        },
        {
            "section": "003",
            "instructor": "Staff",
            "crn": "12347",
            "time": "MW 6:00-7:15",
            "days": "MW",
            "location": "Online"
        }
    ]

    print("Testing section ranking for CSC 3320...")
    ranked = get_ranked_sections("CSC 3320", example_sections)

    print(format_sections_display("CSC 3320", ranked))

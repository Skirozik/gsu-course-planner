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

from datetime import date
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


def _current_term(today: Optional[date] = None) -> str:
    """Return a human-readable label for the current academic term."""
    today = today or date.today()
    if today.month <= 4:
        return f"Spring {today.year}"
    if today.month <= 7:
        return f"Summer {today.year}"
    return f"Fall {today.year}"


# Computed once at import; used as the default term label for section metadata.
DEFAULT_TERM = _current_term()


def get_ranked_sections(course_code: str,
                       sections_data: List[Dict],
                       school: str = "Georgia State University",
                       term: str = None) -> List[SectionRanking]:
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
        term: Semester term (defaults to the current term)

    Returns:
        List of SectionRanking objects sorted by quality (best first)
    """
    term = term or DEFAULT_TERM
    rmp_api = get_rmp_api()

    # Resolve the school once so we query the correct RMP institution. The old
    # code defaulted every batch lookup to GSU, returning wrong (or empty) data
    # for Georgia Tech instructors.
    school_id = (
        rmp_api.GEORGIA_TECH_SCHOOL_ID
        if "tech" in school.lower()
        else rmp_api.GSU_SCHOOL_ID
    )

    # Do exactly ONE RMP lookup per unique normalized instructor. The lookups
    # are lru_cached, so repeated courses taught by the same professor reuse the
    # cached result instead of issuing another rate-limited HTTP request.
    rmp_data_map: Dict[str, Dict] = {}
    seen = set()
    for section in sections_data:
        raw_name = section.get("instructor", "")
        if not raw_name:
            continue

        identity = ProfessorNormalizer.create_identity(raw_name)
        primary = identity.primary_name
        if primary in seen or primary in ("TBA", "Unknown"):
            continue
        seen.add(primary)

        # Search on the normalized "First Last" form (RMP matches it best) and
        # key the result by primary_name so create_ranked_sections finds it.
        result = rmp_api.search_professor(primary, school_id)
        if result:
            rmp_data_map[primary] = result

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
                                   term: str = None) -> Dict[str, List[SectionRanking]]:
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
                    term=term or DEFAULT_TERM
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

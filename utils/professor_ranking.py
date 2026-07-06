"""
Professor Ranking System

Ranks course sections by professor quality using Rate My Professor data.
This is an ADVISORY system only - it ranks options but never blocks sections.

Flow:
  Course → Sections → Instructor Normalization
         → Professor Identity Map
         → Cached RMP Data
         → Ranking Score
         → Sorted Sections Output
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


def generate_rmp_url(professor_id: str) -> str:
    """
    Generate RateMyProfessors profile URL from professor ID

    Args:
        professor_id: RMP professor ID (base64 encoded)

    Returns:
        Full URL to professor's RMP profile
    """
    # RMP URL format: https://www.ratemyprofessors.com/professor/{numeric_id}
    # The ID from API is base64 encoded, we need to extract the numeric part
    # Example ID: "VGVhY2hlci0xMjM0NTY3" decodes to "Teacher-1234567"
    import base64
    try:
        decoded = base64.b64decode(professor_id).decode('utf-8')
        # Extract numeric ID after "Teacher-"
        if 'Teacher-' in decoded:
            numeric_id = decoded.split('Teacher-')[1]
            return f"https://www.ratemyprofessors.com/professor/{numeric_id}"
    except:
        pass

    # Fallback: use the encoded ID directly
    return f"https://www.ratemyprofessors.com/professor/{professor_id}"


def format_instructor_name(name: str) -> str:
    """
    Format instructor name from various formats to "First Last"

    Handles:
    - "Last, First" → "First Last"
    - "Last, First Middle" → "First Middle Last"
    - Already formatted names remain unchanged

    Args:
        name: Instructor name in any format

    Returns:
        Formatted name as "First Last"
    """
    if not name or name in ["Staff", "TBA", "To Be Announced"]:
        return name

    name = name.strip()
    # Strip parenthetical nicknames: "Nemira, Alina (Alina)" -> "Nemira, Alina"
    name = re.sub(r'\s*\([^)]*\)', '', name).strip()

    # Check if name is in "Last, First" format
    if ',' in name:
        parts = [p.strip() for p in name.split(',')]
        if len(parts) == 2:
            last_name, first_name = parts
            # Handle middle names or initials in first_name
            return f"{first_name} {last_name}".strip()

    # Name is already in "First Last" format or some other format
    return name


@dataclass
class ProfessorIdentity:
    """
    Normalized professor identity with aliases
    """
    professor_id: str  # Stable internal ID
    primary_name: str  # Normalized full name
    last_name: str
    first_name: str
    aliases: List[str] = field(default_factory=list)  # Alternative name formats

    def __hash__(self):
        return hash(self.professor_id)


@dataclass
class SectionRanking:
    """
    Course section with RMP data and ranking score
    """
    # Section identifiers
    crn: Optional[str] = None
    course_code: str = ""
    section: str = ""
    term: str = ""

    # Instructor information
    instructor_raw: str = ""  # Original from schedule
    instructor_normalized: str = ""
    professor_id: Optional[str] = None
    rmp_url: Optional[str] = None  # RateMyProfessors profile URL

    # RMP data (advisory)
    rating: Optional[float] = None
    difficulty: Optional[float] = None
    would_take_again: Optional[float] = None
    num_reviews: Optional[int] = None
    match_confidence: float = 0.0  # 0.0 to 1.0

    # Ranking
    score: float = 0.0
    rank: int = 0

    # Additional section details
    time: Optional[str] = None
    days: Optional[str] = None
    location: Optional[str] = None


class ProfessorNormalizer:
    """
    Normalizes professor names and creates identity mappings
    """

    # Common title prefixes to strip
    TITLES = ['dr', 'dr.', 'prof', 'prof.', 'professor', 'mr', 'mr.',
              'mrs', 'mrs.', 'ms', 'ms.', 'miss']

    # Common suffixes
    SUFFIXES = ['jr', 'jr.', 'sr', 'sr.', 'ii', 'iii', 'iv', 'phd', 'ph.d.']

    @classmethod
    def normalize_name(cls, raw_name: str) -> Tuple[str, str, str]:
        """
        Normalize a professor name to standard format

        Args:
            raw_name: Raw name from schedule (e.g., "Smith, John", "Dr. John Smith")

        Returns:
            Tuple of (full_name, last_name, first_name)
        """
        if not raw_name or raw_name.strip().lower() in ['tba', 'staff', 'tbd', 'pending']:
            return ("TBA", "TBA", "TBA")

        # Clean and lowercase for processing
        name = raw_name.strip()
        name_lower = name.lower()

        # Remove titles
        for title in cls.TITLES:
            # Remove title at start with optional period and space
            name_lower = re.sub(rf'\b{re.escape(title)}\s+', '', name_lower)

        # Remove suffixes
        for suffix in cls.SUFFIXES:
            name_lower = re.sub(rf'\s+{re.escape(suffix)}\b', '', name_lower)

        # Remove extra whitespace and punctuation
        name_lower = re.sub(r'[^\w\s-]', ' ', name_lower)
        name_lower = ' '.join(name_lower.split())

        # Parse name format
        if ',' in name_lower:
            # Format: "Last, First" or "Last, First Middle"
            parts = [p.strip() for p in name_lower.split(',')]
            last_name = parts[0]
            first_name = parts[1].split()[0] if len(parts) > 1 else ""
        else:
            # Format: "First Last" or "First Middle Last"
            parts = name_lower.split()
            if len(parts) >= 2:
                first_name = parts[0]
                last_name = parts[-1]
            elif len(parts) == 1:
                last_name = parts[0]
                first_name = ""
            else:
                return ("Unknown", "Unknown", "Unknown")

        # Capitalize properly
        first_name = first_name.capitalize()
        last_name = last_name.capitalize()
        full_name = f"{first_name} {last_name}".strip()

        return (full_name, last_name, first_name)

    @classmethod
    def generate_aliases(cls, last_name: str, first_name: str) -> List[str]:
        """
        Generate common name variations for matching

        Args:
            last_name: Normalized last name
            first_name: Normalized first name

        Returns:
            List of name aliases
        """
        aliases = []

        if not first_name or not last_name:
            return aliases

        # Standard formats
        aliases.append(f"{first_name} {last_name}")
        aliases.append(f"{last_name}, {first_name}")
        aliases.append(f"{last_name} {first_name}")

        # With first initial
        if first_name:
            first_initial = first_name[0]
            aliases.append(f"{first_initial}. {last_name}")
            aliases.append(f"{first_initial} {last_name}")
            aliases.append(f"{last_name}, {first_initial}")

        # Last name only
        aliases.append(last_name)

        return list(set(aliases))  # Remove duplicates

    @classmethod
    def create_identity(cls, raw_name: str) -> ProfessorIdentity:
        """
        Create a professor identity from raw name

        Args:
            raw_name: Raw name from schedule

        Returns:
            ProfessorIdentity object
        """
        full_name, last_name, first_name = cls.normalize_name(raw_name)

        # Generate stable ID (lowercase, no spaces)
        professor_id = f"{last_name.lower()}_{first_name.lower()}".replace(' ', '_')

        # Generate aliases
        aliases = cls.generate_aliases(last_name, first_name)

        return ProfessorIdentity(
            professor_id=professor_id,
            primary_name=full_name,
            last_name=last_name,
            first_name=first_name,
            aliases=aliases
        )


class SectionRanker:
    """
    Ranks course sections by professor quality using RMP data
    """

    # Weights for ranking formula
    RATING_WEIGHT = 20.0
    DIFFICULTY_WEIGHT = -2.0  # Negative because lower is better for students
    REVIEW_CAP = 50  # Cap review bonus to prevent domination

    @classmethod
    def compute_score(cls, rating: Optional[float],
                     difficulty: Optional[float],
                     num_reviews: Optional[int]) -> float:
        """
        Compute ranking score for a professor

        Formula:
          score = (rating * 20) + min(numReviews, 50) - (difficulty * 2)

        Args:
            rating: RMP rating (1-5)
            difficulty: RMP difficulty (1-5)
            num_reviews: Number of RMP reviews

        Returns:
            Ranking score (higher is better)
        """
        if rating is None:
            return 0.0  # No RMP data = lowest score

        score = rating * cls.RATING_WEIGHT

        # Add review bonus (capped)
        if num_reviews:
            review_bonus = min(num_reviews, cls.REVIEW_CAP)
            score += review_bonus

        # Subtract difficulty penalty
        if difficulty:
            score += (difficulty * cls.DIFFICULTY_WEIGHT)

        return round(score, 2)

    @classmethod
    def rank_sections(cls, sections: List[SectionRanking]) -> List[SectionRanking]:
        """
        Sort sections by quality (best professor first)

        Args:
            sections: List of SectionRanking objects

        Returns:
            Sorted list with rank assigned
        """
        # Compute scores for all sections
        for section in sections:
            section.score = cls.compute_score(
                section.rating,
                section.difficulty,
                section.num_reviews
            )

        # Sort by score (descending), then by tiebreakers
        sorted_sections = sorted(
            sections,
            key=lambda s: (
                s.score,  # Primary: higher score is better
                s.num_reviews or 0,  # Tie 1: more reviews
                -(s.difficulty or 5.0),  # Tie 2: lower difficulty (invert for sort)
                s.section  # Tie 3: section number
            ),
            reverse=True
        )

        # Assign ranks
        for rank, section in enumerate(sorted_sections, start=1):
            section.rank = rank

        return sorted_sections

    @classmethod
    def rank_by_course(cls, sections: List[SectionRanking]) -> Dict[str, List[SectionRanking]]:
        """
        Group and rank sections by course code

        Args:
            sections: List of all sections

        Returns:
            Dict mapping course_code to ranked sections
        """
        # Group by course
        by_course = {}
        for section in sections:
            course_code = section.course_code
            if course_code not in by_course:
                by_course[course_code] = []
            by_course[course_code].append(section)

        # Rank each course's sections
        for course_code, course_sections in by_course.items():
            by_course[course_code] = cls.rank_sections(course_sections)

        return by_course


def create_ranked_sections(course_code: str,
                          sections_data: List[Dict],
                          rmp_data_map: Dict[str, Dict],
                          term: str = "Spring 2026") -> List[SectionRanking]:
    """
    Create ranked sections from raw section data and RMP lookups

    Args:
        course_code: Course code (e.g., "CSC 3320")
        sections_data: List of dicts with section info
            [{
                "section": "001",
                "instructor": "Smith, John",
                "crn": "12345",
                "time": "MWF 10:00-10:50",
                "days": "MWF",
                "location": "Room 123"
            }, ...]
        rmp_data_map: Dict mapping normalized names to RMP data
            {
                "John Smith": {
                    "rating": 4.5,
                    "difficulty": 3.2,
                    "num_reviews": 45,
                    ...
                }
            }
        term: Semester term

    Returns:
        List of ranked SectionRanking objects
    """
    sections = []

    for section_data in sections_data:
        # Get raw instructor name
        instructor_raw = section_data.get("instructor", "TBA")

        # Normalize instructor
        identity = ProfessorNormalizer.create_identity(instructor_raw)

        # Try to find RMP data
        rmp_data = None
        match_confidence = 0.0

        if identity.primary_name != "TBA":
            # Try exact match first
            if identity.primary_name in rmp_data_map:
                rmp_data = rmp_data_map[identity.primary_name]
                match_confidence = 1.0
            else:
                # Try aliases
                for alias in identity.aliases:
                    if alias in rmp_data_map:
                        rmp_data = rmp_data_map[alias]
                        match_confidence = 0.8
                        break

        # Format instructor name from "Last, First" to "First Last"
        formatted_name = format_instructor_name(instructor_raw)

        # Generate RMP URL if we have RMP data
        rmp_url = None
        if rmp_data and rmp_data.get("id"):
            rmp_url = generate_rmp_url(rmp_data["id"])

        # Create section ranking
        section_ranking = SectionRanking(
            crn=section_data.get("crn"),
            course_code=course_code,
            section=section_data.get("section", ""),
            term=term,
            instructor_raw=instructor_raw,
            instructor_normalized=formatted_name,
            professor_id=identity.professor_id,
            rmp_url=rmp_url,
            rating=rmp_data.get("rating") if rmp_data else None,
            difficulty=rmp_data.get("difficulty") if rmp_data else None,
            would_take_again=rmp_data.get("would_take_again") if rmp_data else None,
            num_reviews=(rmp_data.get("num_reviews") or rmp_data.get("num_ratings")) if rmp_data else None,
            match_confidence=match_confidence,
            time=section_data.get("time"),
            days=section_data.get("days"),
            location=section_data.get("location")
        )

        sections.append(section_ranking)

    # Rank sections
    ranked = SectionRanker.rank_sections(sections)

    return ranked


def format_ranking_display(section: SectionRanking) -> str:
    """
    Format a ranked section for display

    Args:
        section: SectionRanking object

    Returns:
        Formatted string
    """
    lines = []

    # Header with rank
    rank_emoji = "🥇" if section.rank == 1 else "🥈" if section.rank == 2 else "🥉" if section.rank == 3 else f"#{section.rank}"
    lines.append(f"{rank_emoji} Section {section.section} - {section.instructor_normalized}")

    # RMP data if available
    if section.rating:
        rating_emoji = "🌟" if section.rating >= 4.5 else "⭐" if section.rating >= 4.0 else "✨" if section.rating >= 3.5 else "💫"
        lines.append(f"   {rating_emoji} Rating: {section.rating}/5.0 ({section.num_reviews} reviews)")

        if section.difficulty:
            diff_emoji = "😊" if section.difficulty <= 2.5 else "😐" if section.difficulty <= 3.5 else "😰"
            lines.append(f"   {diff_emoji} Difficulty: {section.difficulty}/5.0")

        if section.would_take_again:
            lines.append(f"   👍 {section.would_take_again}% would take again")

        lines.append(f"   📊 Quality Score: {section.score}")
    else:
        lines.append(f"   ⚠️ No RMP data available")

    # Section details
    if section.time:
        lines.append(f"   🕐 {section.time}")
    if section.location:
        lines.append(f"   📍 {section.location}")

    return "\n".join(lines)

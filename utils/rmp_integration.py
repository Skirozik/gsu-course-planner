"""
Rate My Professor Integration

Fetches professor ratings from RateMyProfessors.com to help students
make informed decisions about course selection.

Note: Uses public RMP GraphQL API (no official API key required)
"""

import requests
import json
from typing import Dict, List, Optional
import time
from functools import lru_cache

import logging
logger = logging.getLogger(__name__)


class RateMyProfessorAPI:
    """
    Client for Rate My Professor data

    Uses RMP's public GraphQL endpoint to fetch professor ratings.
    Implements caching and rate limiting to be respectful.
    """

    BASE_URL = "https://www.ratemyprofessors.com/graphql"

    # GSU School ID on RateMyProfessors
    GSU_SCHOOL_ID = "U2Nob29sLTM2MA=="  # Georgia State University (School ID: 360)
    GEORGIA_TECH_SCHOOL_ID = "U2Nob29sLTM1MQ=="  # Georgia Tech

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Content-Type": "application/json",
        "Authorization": "Basic dGVzdDp0ZXN0"  # Public auth token
    }

    REQUEST_DELAY = 0.5  # Be nice to their servers

    def __init__(self):
        self.last_request_time = 0
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def _rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.REQUEST_DELAY:
            time.sleep(self.REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    @lru_cache(maxsize=500)
    def search_professor(self, professor_name: str, school_id: str = None) -> Optional[Dict]:
        """
        Search for a professor by name at a specific school

        Args:
            professor_name: Full name or last name of professor
            school_id: RMP school ID (defaults to GSU)

        Returns:
            Dict with professor data or None if not found
        """
        if school_id is None:
            school_id = self.GSU_SCHOOL_ID

        # Clean professor name
        name = professor_name.strip()

        # GraphQL query to search for professor
        query = """
        query NewSearchTeachersQuery($text: String!, $schoolID: ID!) {
          newSearch {
            teachers(query: {text: $text, schoolID: $schoolID}) {
              edges {
                node {
                  id
                  firstName
                  lastName
                  avgRating
                  avgDifficulty
                  numRatings
                  wouldTakeAgainPercent
                  department
                }
              }
            }
          }
        }
        """

        variables = {
            "text": name,
            "schoolID": school_id
        }

        try:
            self._rate_limit()
            response = self.session.post(
                self.BASE_URL,
                json={"query": query, "variables": variables},
                timeout=10
            )

            if response.status_code != 200:
                logger.warning(f"RMP API returned {response.status_code} for {name}")
                return None

            data = response.json()

            # Extract professor data
            edges = data.get("data", {}).get("newSearch", {}).get("teachers", {}).get("edges", [])

            if not edges:
                logger.info(f"No RMP data found for professor: {name}")
                return None

            # Get first match (usually most relevant)
            prof_data = edges[0]["node"]

            return {
                "id": prof_data["id"],
                "name": f"{prof_data['firstName']} {prof_data['lastName']}",
                "rating": round(prof_data["avgRating"], 1) if prof_data["avgRating"] else None,
                "difficulty": round(prof_data["avgDifficulty"], 1) if prof_data["avgDifficulty"] else None,
                "num_ratings": prof_data["numRatings"],
                "would_take_again": round(prof_data["wouldTakeAgainPercent"]) if prof_data["wouldTakeAgainPercent"] else None,
                "department": prof_data["department"]
            }

        except Exception as e:
            logger.error(f"Error fetching RMP data for {name}: {e}")
            return None

    def get_professor_rating(self, professor_name: str, school: str = "Georgia State University") -> Optional[Dict]:
        """
        Convenience method to get professor rating with school name

        Args:
            professor_name: Professor's name
            school: School name ("Georgia State University" or "Georgia Tech")

        Returns:
            Professor rating data or None
        """
        school_id = self.GEORGIA_TECH_SCHOOL_ID if "tech" in school.lower() else self.GSU_SCHOOL_ID
        return self.search_professor(professor_name, school_id)

    def search_all_professors(self, professor_name: str, school_id: str = None) -> List[Dict]:
        """
        Search for ALL matching professors (not just first match)

        Args:
            professor_name: Full name or last name of professor
            school_id: RMP school ID (defaults to GSU)

        Returns:
            List of professor data dicts (empty list if none found)
        """
        if school_id is None:
            school_id = self.GSU_SCHOOL_ID

        name = professor_name.strip()

        query = """
        query NewSearchTeachersQuery($text: String!, $schoolID: ID!) {
          newSearch {
            teachers(query: {text: $text, schoolID: $schoolID}) {
              edges {
                node {
                  id
                  firstName
                  lastName
                  avgRating
                  avgDifficulty
                  numRatings
                  wouldTakeAgainPercent
                  department
                }
              }
            }
          }
        }
        """

        variables = {
            "text": name,
            "schoolID": school_id
        }

        try:
            self._rate_limit()
            response = self.session.post(
                self.BASE_URL,
                json={"query": query, "variables": variables},
                timeout=10
            )

            if response.status_code != 200:
                logger.warning(f"RMP API returned {response.status_code} for {name}")
                return []

            data = response.json()
            edges = data.get("data", {}).get("newSearch", {}).get("teachers", {}).get("edges", [])

            if not edges:
                return []

            # Return ALL matches
            professors = []
            for edge in edges:
                prof_data = edge["node"]
                professors.append({
                    "id": prof_data["id"],
                    "name": f"{prof_data['firstName']} {prof_data['lastName']}",
                    "rating": round(prof_data["avgRating"], 1) if prof_data["avgRating"] else None,
                    "difficulty": round(prof_data["avgDifficulty"], 1) if prof_data["avgDifficulty"] else None,
                    "num_ratings": prof_data["numRatings"],
                    "would_take_again": round(prof_data["wouldTakeAgainPercent"]) if prof_data["wouldTakeAgainPercent"] else None,
                    "department": prof_data["department"]
                })

            return professors

        except Exception as e:
            logger.error(f"Error fetching RMP data for {name}: {e}")
            return []

    def batch_search_professors(self, professor_names: List[str], school_id: str = None) -> Dict[str, Dict]:
        """
        Search for multiple professors and return mapping

        Args:
            professor_names: List of professor names
            school_id: RMP school ID (defaults to GSU)

        Returns:
            Dict mapping professor name to RMP data (best match per name)
        """
        results = {}

        for name in professor_names:
            if not name or name.strip().lower() in ['tba', 'staff', 'tbd']:
                continue

            # Get best match (first result)
            prof_data = self.search_professor(name, school_id)
            if prof_data:
                results[name] = prof_data

        return results

    def get_rating_emoji(self, rating: Optional[float]) -> str:
        """Get emoji representation of rating"""
        if rating is None:
            return "❓"
        elif rating >= 4.5:
            return "🌟"
        elif rating >= 4.0:
            return "⭐"
        elif rating >= 3.5:
            return "✨"
        elif rating >= 3.0:
            return "⚡"
        else:
            return "💫"

    def get_difficulty_emoji(self, difficulty: Optional[float]) -> str:
        """Get emoji representation of difficulty"""
        if difficulty is None:
            return "❓"
        elif difficulty <= 2.0:
            return "😊"  # Easy
        elif difficulty <= 3.0:
            return "😐"  # Moderate
        elif difficulty <= 4.0:
            return "😰"  # Challenging
        else:
            return "💀"  # Very difficult


# Singleton instance
_rmp_api = None

def get_rmp_api() -> RateMyProfessorAPI:
    """Get singleton RMP API instance"""
    global _rmp_api
    if _rmp_api is None:
        _rmp_api = RateMyProfessorAPI()
    return _rmp_api


def enrich_courses_with_rmp(courses: List[Dict], school: str = "Georgia State University") -> List[Dict]:
    """
    Enrich course data with RMP ratings

    Args:
        courses: List of course dicts (must have 'professor' or 'instructor' field)
        school: School name for RMP lookup

    Returns:
        Same courses with added 'rmp_data' field
    """
    api = get_rmp_api()

    for course in courses:
        # Try to get professor name from various fields
        prof_name = course.get("professor") or course.get("instructor") or course.get("prof_name")

        if prof_name and prof_name.lower() not in ["staff", "tba", "tbd", ""]:
            rmp_data = api.get_professor_rating(prof_name, school)
            course["rmp_data"] = rmp_data
        else:
            course["rmp_data"] = None

    return courses


def format_rmp_display(rmp_data: Optional[Dict]) -> str:
    """
    Format RMP data for display

    Args:
        rmp_data: RMP data dict from search_professor

    Returns:
        Formatted string for display
    """
    if not rmp_data:
        return "No ratings available"

    api = get_rmp_api()

    rating = rmp_data.get("rating")
    difficulty = rmp_data.get("difficulty")
    num_ratings = rmp_data.get("num_ratings", 0)
    would_take_again = rmp_data.get("would_take_again")

    parts = []

    if rating:
        emoji = api.get_rating_emoji(rating)
        parts.append(f"{emoji} {rating}/5.0")

    if difficulty:
        emoji = api.get_difficulty_emoji(difficulty)
        parts.append(f"{emoji} Difficulty: {difficulty}/5.0")

    if would_take_again:
        parts.append(f"👍 {would_take_again}% would take again")

    if num_ratings:
        parts.append(f"({num_ratings} ratings)")

    return " | ".join(parts) if parts else "No ratings available"


# Demo/testing function
def demo_rmp_lookup():
    """Demo RMP integration"""
    print("=" * 70)
    print("RATE MY PROFESSOR INTEGRATION DEMO")
    print("=" * 70 + "\n")

    api = get_rmp_api()

    # Test with some GSU CS professors (replace with real names)
    test_professors = [
        "Ashok Goel",  # Famous AI professor
        "Smith",  # Common last name
        "Johnson"  # Another common name
    ]

    for prof_name in test_professors:
        print(f"\nSearching for: {prof_name}")
        print("-" * 70)

        rmp_data = api.get_professor_rating(prof_name)

        if rmp_data:
            print(f"Found: {rmp_data['name']}")
            print(f"  Department: {rmp_data['department']}")
            print(f"  {format_rmp_display(rmp_data)}")
        else:
            print("  Not found in RMP database")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    demo_rmp_lookup()

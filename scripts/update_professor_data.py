"""
Professor Data Pre-Warm Script

Pre-populates the persistent Rate My Professors cache so the app rarely has to
hit RMP live during a user session.

How it works:
1. Pull the current term's sections from the school's live Banner API.
2. Extract and normalize every real instructor name.
3. Look each one up via the RMP client, which writes results through to the
   on-disk cache (data/rmp_cache.json).

Run it periodically (e.g. before each registration period):
    python scripts/update_professor_data.py                 # GSU (default subjects)
    python scripts/update_professor_data.py --school "Georgia Tech"
    python scripts/update_professor_data.py --subjects CSC MATH CIS
"""

import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from typing import List, Optional

from utils.rmp_integration import get_rmp_api
from utils.gsu_banner_api import GSUBannerAPI
from utils.gatech_banner_api import GATechBannerAPI
from utils.professor_ranking import ProfessorNormalizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sensible default subjects to warm per school.
DEFAULT_SUBJECTS = {
    "Georgia State University": ["CSC", "MATH", "CIS", "ITEC", "ACCT", "ECON"],
    "Georgia Tech": ["CS", "MATH"],
}


class ProfessorDataUpdater:
    """Pre-warms the persistent RMP cache from live Banner schedule data."""

    def __init__(self, school: str = "Georgia State University",
                 subjects: Optional[List[str]] = None):
        self.school = school
        self.subjects = subjects or DEFAULT_SUBJECTS.get(school, ["CSC"])
        self.rmp_api = get_rmp_api()
        self.banner_api = (
            GATechBannerAPI() if "tech" in school.lower() else GSUBannerAPI()
        )

    def get_all_professors_from_schedule(self, term: Optional[str] = None) -> List[str]:
        """
        Extract all unique, normalized instructor names from the live schedule.

        Args:
            term: Banner term code (defaults to the current term).

        Returns:
            Sorted list of normalized "First Last" professor names.
        """
        if term is None:
            term = self.banner_api.get_current_term()

        logger.info(f"Fetching {self.school} schedule for term {term} "
                    f"({len(self.subjects)} subjects)...")

        names = set()
        for subject in self.subjects:
            try:
                sections = self.banner_api.get_all_sections(term, subject)
            except Exception as e:
                logger.warning(f"  Could not fetch sections for {subject}: {e}")
                continue

            for section in sections:
                raw = section.get("instructor", "")
                if not raw:
                    continue
                full_name, _, _ = ProfessorNormalizer.normalize_name(raw)
                if full_name and full_name not in ("TBA", "Unknown"):
                    names.add(full_name)

            logger.info(f"  {subject}: {len(sections)} sections")

        return sorted(names)

    def update_rmp_data(self, professors: List[str]) -> int:
        """
        Look up each professor via RMP (results are cached to disk by the client).

        Returns:
            Number of professors for which RMP data was found.
        """
        logger.info(f"Looking up RMP data for {len(professors)} professors...")

        found = 0
        for i, professor in enumerate(professors, 1):
            try:
                rmp_data = self.rmp_api.get_professor_rating(professor, self.school)
                if rmp_data:
                    found += 1
                    logger.info(f"[{i}/{len(professors)}] {professor}: "
                                f"{rmp_data.get('rating')}/5.0")
                else:
                    logger.info(f"[{i}/{len(professors)}] {professor}: not found")
            except Exception as e:
                logger.error(f"[{i}/{len(professors)}] {professor}: error - {e}")

        return found

    def run_update(self):
        """Run the full pre-warm process."""
        logger.info("=" * 70)
        logger.info(f"Pre-warming RMP cache for {self.school}")
        logger.info("=" * 70)

        professors = self.get_all_professors_from_schedule()
        logger.info(f"Found {len(professors)} unique instructors this term")

        if not professors:
            logger.warning("No instructors found — is the term open and the "
                           "Banner API reachable? Nothing to update.")
            return

        found = self.update_rmp_data(professors)

        stats = self.rmp_api.cache_stats()
        logger.info("=" * 70)
        logger.info(f"✅ Done. {found}/{len(professors)} matched RMP this run.")
        logger.info(f"📊 Cache now holds {stats['total']} entries "
                    f"({stats['with_rating']} with ratings) at {self.rmp_api.cache_file}")
        logger.info("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Pre-warm the RMP professor cache.")
    parser.add_argument("--school", default="Georgia State University",
                        choices=["Georgia State University", "Georgia Tech"],
                        help="School to pull schedule data from.")
    parser.add_argument("--subjects", nargs="+", default=None,
                        help="Subject codes to warm (default: a per-school list).")
    args = parser.parse_args()

    updater = ProfessorDataUpdater(school=args.school, subjects=args.subjects)
    updater.run_update()


if __name__ == "__main__":
    main()

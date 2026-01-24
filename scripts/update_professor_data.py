"""
Automated Professor Data Update Script

Runs periodically to:
1. Fetch latest GSU course schedule
2. Extract unique professor names
3. Update RMP data for all professors
4. Cache results for fast app performance

Schedule: Run daily during registration period, weekly otherwise
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.rmp_integration import get_rmp_api
from utils.gsu_schedule_scraper import GSUScheduleScraper
import json
from datetime import datetime
from typing import Dict, List
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProfessorDataUpdater:
    """
    Updates professor RMP data automatically
    """

    def __init__(self, cache_file: str = "data/professor_cache.json"):
        self.cache_file = cache_file
        self.rmp_api = get_rmp_api()
        self.scraper = GSUScheduleScraper()

    def load_cache(self) -> Dict:
        """Load cached professor data"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}

    def save_cache(self, data: Dict):
        """Save professor data to cache"""
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_all_professors_from_schedule(self, term: str = None) -> List[str]:
        """
        Extract all unique professor names from GSU schedule

        Args:
            term: Term code (optional)

        Returns:
            List of professor names
        """
        # Get all courses being offered this term
        # This would require scraping the entire schedule or using an API

        # For now, return demo list - replace with actual scraping
        logger.info("Fetching professor list from GSU schedule...")

        # TODO: Implement actual schedule scraping
        # professors = self.scraper.get_all_professors(term)

        # Placeholder - replace with real data
        professors = [
            "Robert Robinson", "Sarah Chen", "David Kim",
            "Emily Rodriguez", "Daniel Taylor", "Andrew King",
            # ... all professors teaching this term
        ]

        return professors

    def update_rmp_data(self, professors: List[str], school: str = "Georgia State University") -> Dict:
        """
        Fetch RMP data for all professors

        Args:
            professors: List of professor names
            school: School name

        Returns:
            Dict mapping professor names to RMP data
        """
        logger.info(f"Updating RMP data for {len(professors)} professors...")

        results = {}

        for i, professor in enumerate(professors, 1):
            logger.info(f"[{i}/{len(professors)}] Fetching: {professor}")

            try:
                rmp_data = self.rmp_api.get_professor_rating(professor, school)

                if rmp_data:
                    results[professor] = {
                        **rmp_data,
                        "last_updated": datetime.now().isoformat()
                    }
                    logger.info(f"  ✅ Found: {rmp_data.get('rating')}/5.0")
                else:
                    logger.info(f"  ⚠️ Not found in RMP")

                # Rate limiting
                time.sleep(0.6)

            except Exception as e:
                logger.error(f"  ❌ Error: {e}")

        return results

    def run_update(self):
        """
        Run full update process
        """
        logger.info("=" * 70)
        logger.info("Starting Professor Data Update")
        logger.info("=" * 70)

        # Load existing cache
        cache = self.load_cache()
        logger.info(f"Loaded cache with {len(cache)} professors")

        # Get current professors
        current_professors = self.get_all_professors_from_schedule()
        logger.info(f"Found {len(current_professors)} professors this term")

        # Update RMP data
        updated_data = self.update_rmp_data(current_professors)

        # Merge with cache (keep old data, update with new)
        cache.update(updated_data)

        # Save cache
        self.save_cache(cache)
        logger.info(f"✅ Cache updated: {len(cache)} total professors")

        # Summary
        with_rmp = sum(1 for v in cache.values() if v.get('rating') is not None)
        logger.info(f"📊 Summary: {with_rmp}/{len(cache)} have RMP data ({with_rmp/len(cache)*100:.1f}%)")

        logger.info("=" * 70)
        logger.info("Update Complete!")
        logger.info("=" * 70)


def main():
    """Run the update script"""
    updater = ProfessorDataUpdater()
    updater.run_update()


if __name__ == "__main__":
    main()

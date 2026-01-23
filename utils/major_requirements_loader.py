"""
Major Requirements Loader

Loads and integrates major program requirements with course catalog data.

Provides API for:
- Loading major requirements
- Linking requirements to course metadata
- Checking student progress against major requirements
- Getting next required courses for a major
"""

import json
from typing import Dict, List, Optional
from pathlib import Path


class MajorRequirementsLoader:
    """
    Loads and manages major program requirements data.

    Integrates with course catalog to provide comprehensive
    degree planning information.
    """

    def __init__(self, requirements_dir: str = None):
        """
        Initialize loader.

        Args:
            requirements_dir: Directory with major requirements JSON files
        """
        if requirements_dir is None:
            base_dir = Path(__file__).parent.parent
            requirements_dir = base_dir / "data" / "major_requirements"

        self.requirements_dir = Path(requirements_dir)
        self._majors = {}
        self._loaded = False

    def load_all_majors(self):
        """Load all major requirements from JSON files"""
        if not self.requirements_dir.exists():
            print(f"Requirements directory not found: {self.requirements_dir}")
            return

        # Load all JSON files in requirements directory
        for json_file in self.requirements_dir.glob("*.json"):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Handle both single major and array of majors
                    if isinstance(data, list):
                        majors_list = data
                    else:
                        majors_list = [data]

                    for major_data in majors_list:
                        major_name = major_data.get("major_name")
                        if major_name:
                            self._majors[major_name] = major_data
                            print(f"[+] Loaded major: {major_name}")

            except Exception as e:
                print(f"Error loading {json_file}: {e}")

        self._loaded = True

    def get_major(self, major_name: str) -> Optional[Dict]:
        """
        Get major requirements by name.

        Args:
            major_name: Name of major

        Returns:
            Major requirements dict or None
        """
        if not self._loaded:
            self.load_all_majors()

        return self._majors.get(major_name)

    def get_all_majors(self) -> List[str]:
        """Get list of all available major names"""
        if not self._loaded:
            self.load_all_majors()

        return list(self._majors.keys())

    def get_required_courses_for_major(self, major_name: str) -> List[str]:
        """
        Get flat list of all required course codes for a major.

        Args:
            major_name: Name of major

        Returns:
            List of course codes
        """
        major = self.get_major(major_name)
        if not major:
            return []

        courses = []
        required_courses = major.get("required_courses", {})

        for category, course_list in required_courses.items():
            courses.extend(course_list)

        return courses

    def get_requirements_by_category(self, major_name: str) -> Dict[str, List[str]]:
        """
        Get required courses organized by category.

        Args:
            major_name: Name of major

        Returns:
            Dict of category -> course codes
        """
        major = self.get_major(major_name)
        if not major:
            return {}

        return major.get("required_courses", {})

    def get_elective_groups(self, major_name: str) -> List[Dict]:
        """
        Get elective groups for a major.

        Args:
            major_name: Name of major

        Returns:
            List of elective group dicts
        """
        major = self.get_major(major_name)
        if not major:
            return []

        return major.get("elective_groups", [])

    def check_major_progress(
        self,
        major_name: str,
        completed_courses: List[str]
    ) -> Dict:
        """
        Check student's progress toward major requirements.

        Args:
            major_name: Name of major
            completed_courses: List of completed course codes

        Returns:
            Dict with progress information
        """
        major = self.get_major(major_name)
        if not major:
            return {
                "error": "Major not found",
                "major_name": major_name
            }

        completed_set = {c.upper().strip() for c in completed_courses}
        required_courses = major.get("required_courses", {})

        # Calculate progress by category
        category_progress = {}
        total_required = 0
        total_completed = 0

        for category, course_list in required_courses.items():
            category_total = len(course_list)
            category_completed = sum(
                1 for course in course_list
                if course.upper().strip() in completed_set
            )

            category_progress[category] = {
                "total": category_total,
                "completed": category_completed,
                "remaining": category_total - category_completed,
                "percentage": int((category_completed / category_total * 100) if category_total > 0 else 0)
            }

            total_required += category_total
            total_completed += category_completed

        # Overall progress
        overall_percentage = int((total_completed / total_required * 100) if total_required > 0 else 0)

        return {
            "major_name": major_name,
            "degree_type": major.get("degree_type", ""),
            "total_required_courses": total_required,
            "total_completed_courses": total_completed,
            "overall_progress_percentage": overall_percentage,
            "category_progress": category_progress,
            "total_hours": major.get("total_hours", 120)
        }

    def get_next_required_courses(
        self,
        major_name: str,
        completed_courses: List[str],
        in_progress_courses: List[str] = None
    ) -> Dict[str, List[str]]:
        """
        Get next required courses student should take.

        Args:
            major_name: Name of major
            completed_courses: Completed course codes
            in_progress_courses: Currently enrolled course codes

        Returns:
            Dict of category -> list of needed course codes
        """
        if in_progress_courses is None:
            in_progress_courses = []

        major = self.get_major(major_name)
        if not major:
            return {}

        completed_set = {c.upper().strip() for c in completed_courses}
        in_progress_set = {c.upper().strip() for c in in_progress_courses}
        all_taken = completed_set | in_progress_set

        required_courses = major.get("required_courses", {})
        next_courses = {}

        for category, course_list in required_courses.items():
            needed = [
                course for course in course_list
                if course.upper().strip() not in all_taken
            ]

            if needed:
                next_courses[category] = needed

        return next_courses

    def get_major_metadata(self, major_name: str) -> Dict:
        """
        Get major metadata (name, degree, college, etc).

        Args:
            major_name: Name of major

        Returns:
            Dict with metadata
        """
        major = self.get_major(major_name)
        if not major:
            return {}

        return {
            "major_name": major.get("major_name", ""),
            "degree_type": major.get("degree_type", ""),
            "college": major.get("college", ""),
            "catalog_year": major.get("catalog_year", ""),
            "total_hours": major.get("total_hours", 120),
            "progression_notes": major.get("progression_notes", ""),
            "restrictions": major.get("restrictions", "")
        }

    def link_with_course_data(self, major_name: str, catalog_loader) -> Dict:
        """
        Link major requirements with course metadata from catalog.

        Args:
            major_name: Name of major
            catalog_loader: CatalogLoader instance

        Returns:
            Dict with requirements enhanced with course details
        """
        major = self.get_major(major_name)
        if not major:
            return {}

        required_courses = major.get("required_courses", {})
        enhanced_requirements = {}

        for category, course_list in required_courses.items():
            enhanced_courses = []

            for course_code in course_list:
                # Try to get course details from catalog
                # This would require catalog_loader to have a get_course method
                course_info = {
                    "course_code": course_code,
                    "course_name": "",  # Would fetch from catalog
                    "credits": 3,  # Would fetch from catalog
                    "description": ""  # Would fetch from catalog
                }

                enhanced_courses.append(course_info)

            enhanced_requirements[category] = enhanced_courses

        return {
            "major_name": major_name,
            "requirements": enhanced_requirements,
            "elective_groups": major.get("elective_groups", []),
            "metadata": self.get_major_metadata(major_name)
        }


# Global loader instance
_requirements_loader: Optional[MajorRequirementsLoader] = None


def get_major_requirements_loader() -> MajorRequirementsLoader:
    """Get singleton MajorRequirementsLoader instance"""
    global _requirements_loader
    if _requirements_loader is None:
        _requirements_loader = MajorRequirementsLoader()
        _requirements_loader.load_all_majors()
    return _requirements_loader

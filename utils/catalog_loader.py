"""
Catalog Loader Module
Dynamically loads course catalogs from JSON files
Supports multiple majors and degree programs
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class CatalogLoader:
    """Loads and manages course catalogs for different majors"""
    
    def __init__(self, catalog_dir: str = None):
        """
        Initialize the catalog loader
        
        Args:
            catalog_dir: Directory containing catalog JSON files.
                        If None, uses default data/course_catalogs/
        """
        if catalog_dir is None:
            # Get the project root directory
            current_dir = Path(__file__).parent.parent  # Go up from utils/
            catalog_dir = current_dir / "data" / "course_catalogs"
        
        self.catalog_dir = Path(catalog_dir)
        self.catalogs: Dict[str, Dict] = {}
        self.load_all_catalogs()
    
    def load_all_catalogs(self) -> None:
        """Load all JSON catalog files from the catalog directory"""
        if not self.catalog_dir.exists():
            print(f"Warning: Catalog directory not found: {self.catalog_dir}")
            return
        
        json_files = self.catalog_dir.glob("*.json")
        for json_file in json_files:
            major_name = json_file.stem  # filename without extension
            try:
                with open(json_file, 'r') as f:
                    catalog_data = json.load(f)
                    # Store by major name for easy lookup
                    major_key = catalog_data.get("metadata", {}).get("major", major_name)
                    self.catalogs[major_key] = catalog_data
                    print(f"[+] Loaded catalog: {major_key}")
            except json.JSONDecodeError as e:
                print(f"[!] Error loading {json_file}: {e}")
            except Exception as e:
                print(f"[!] Unexpected error loading {json_file}: {e}")
    
    def get_available_majors(self) -> List[str]:
        """Get list of available majors"""
        return sorted(list(self.catalogs.keys()))
    
    def get_catalog(self, major: str) -> Optional[Dict]:
        """Get the full catalog for a specific major"""
        return self.catalogs.get(major)
    
    def get_degree_requirements(self, major: str) -> Optional[Dict]:
        """Get degree requirements for a major"""
        catalog = self.catalogs.get(major)
        if catalog:
            return catalog.get("degree_requirements", {})
        return None
    
    def get_core_courses(self, major: str) -> List[Dict]:
        """Get list of required core courses for a major"""
        requirements = self.get_degree_requirements(major)
        if requirements:
            return requirements.get("core_courses", [])
        return []
    
    def get_elective_courses(self, major: str) -> List[Dict]:
        """Get list of elective courses for a major"""
        requirements = self.get_degree_requirements(major)
        if requirements:
            return requirements.get("electives", [])
        return []
    
    def get_math_requirements(self, major: str) -> List[Dict]:
        """Get list of math requirements for a major"""
        requirements = self.get_degree_requirements(major)
        if requirements:
            return requirements.get("math_requirements", [])
        return []
    
    def get_all_courses_for_major(self, major: str) -> Dict:
        """Get all courses (with prerequisites) for a major"""
        catalog = self.catalogs.get(major)
        if catalog:
            return catalog.get("courses", {})
        return {}
    
    def get_course_info(self, major: str, course_code: str) -> Optional[Dict]:
        """Get detailed info for a specific course in a major's catalog"""
        course_code = course_code.upper().strip()
        courses = self.get_all_courses_for_major(major)
        return courses.get(course_code)
    
    def get_prerequisites(self, major: str, course_code: str) -> List[str]:
        """Get prerequisites for a course in a specific major"""
        course = self.get_course_info(major, course_code)
        if course:
            return course.get("prerequisites", [])
        return []
    
    def get_corequisites(self, major: str, course_code: str) -> List[str]:
        """Get corequisites for a course in a specific major"""
        course = self.get_course_info(major, course_code)
        if course:
            return course.get("corequisites", [])
        return []
    
    def check_prerequisites_met(
        self, major: str, course_code: str, completed_courses: List[str]
    ) -> Dict:
        """
        Check if prerequisites are met for a course in a specific major
        
        Args:
            major: Major/degree program
            course_code: Code of the course to check
            completed_courses: List of completed course codes
        
        Returns:
            Dict with can_take (bool), met, missing prerequisites
        """
        course_code = course_code.upper().strip()
        completed_upper = [c.upper().strip() for c in completed_courses]
        
        prereqs = self.get_prerequisites(major, course_code)
        met = [p for p in prereqs if p in completed_upper]
        missing = [p for p in prereqs if p not in completed_upper]
        
        return {
            "can_take": len(missing) == 0,
            "met": met,
            "missing": missing,
            "all_prerequisites": prereqs
        }
    
    def get_courses_unlocked_by(self, major: str, course_code: str) -> List[str]:
        """Get courses that have this course as a prerequisite in a major"""
        course_code = course_code.upper().strip()
        unlocked = []
        courses = self.get_all_courses_for_major(major)
        
        for code, info in courses.items():
            if course_code in info.get("prerequisites", []):
                unlocked.append(code)
        
        return unlocked
    
    def get_all_prerequisites(
        self, major: str, course_code: str, visited: set = None
    ) -> List[str]:
        """
        Get all prerequisites recursively (the full prerequisite chain)
        Returns courses in order they should be taken
        """
        if visited is None:
            visited = set()
        
        course_code = course_code.upper().strip()
        
        if course_code in visited:
            return []
        
        visited.add(course_code)
        all_prereqs = []
        
        direct_prereqs = self.get_prerequisites(major, course_code)
        for prereq in direct_prereqs:
            # Get prerequisites of prerequisites first
            deeper_prereqs = self.get_all_prerequisites(major, prereq, visited)
            for p in deeper_prereqs:
                if p not in all_prereqs:
                    all_prereqs.append(p)
            # Then add this prerequisite
            if prereq not in all_prereqs:
                all_prereqs.append(prereq)
        
        return all_prereqs
    
    def get_recommended_next_courses(
        self, major: str, completed_courses: List[str], limit: int = 5
    ) -> List[Dict]:
        """
        Get recommended next courses a student can take
        
        Args:
            major: Student's major
            completed_courses: List of courses they've completed
            limit: Max number of recommendations to return
        
        Returns:
            List of courses they can now take, prioritized by prerequisites met
        """
        completed_upper = [c.upper().strip() for c in completed_courses]
        courses = self.get_all_courses_for_major(major)
        
        available = []
        
        for course_code, course_info in courses.items():
            # Skip if already taken
            if course_code in completed_upper:
                continue
            
            # Check if prerequisites are met
            prereqs_result = self.check_prerequisites_met(
                major, course_code, completed_courses
            )
            
            if prereqs_result["can_take"]:
                available.append({
                    "course_code": course_code,
                    "course_name": course_info.get("name", "Unknown"),
                    "credits": course_info.get("credits", 0),
                    "description": course_info.get("description", ""),
                    "prerequisites": prereqs_result["met"],
                    "is_core": False  # TODO: determine if core/elective
                })
        
        # Sort by course code (could add more sophisticated sorting)
        available.sort(key=lambda x: x["course_code"])
        
        return available[:limit]
    
    def get_degree_progress(
        self, major: str, completed_courses: List[str]
    ) -> Dict:
        """
        Calculate student's degree progress
        
        Args:
            major: Student's major
            completed_courses: List of completed course codes
        
        Returns:
            Dict with progress metrics
        """
        completed_upper = [c.upper().strip() for c in completed_courses]
        core_courses = self.get_core_courses(major)
        math_requirements = self.get_math_requirements(major)
        
        total_core = len(core_courses)
        completed_core = sum(1 for c in core_courses if c["course_code"] in completed_upper)
        
        total_math = len(math_requirements)
        completed_math = sum(1 for m in math_requirements if m["course_code"] in completed_upper)
        
        catalog = self.get_catalog(major)
        total_credits_required = catalog.get("metadata", {}).get("total_credits_required", 120)
        
        # Calculate completed credits (simplified - would need course details)
        completed_credits = len(completed_courses) * 3  # Rough estimate
        
        return {
            "major": major,
            "core_progress": f"{completed_core}/{total_core}",
            "math_progress": f"{completed_math}/{total_math}",
            "total_credits_required": total_credits_required,
            "estimated_completed_credits": completed_credits,
            "completion_percentage": min(100, int((completed_credits / total_credits_required) * 100))
        }


# Global catalog loader instance
_loader: Optional[CatalogLoader] = None


def get_catalog_loader() -> CatalogLoader:
    """Get or create the global catalog loader instance"""
    global _loader
    if _loader is None:
        _loader = CatalogLoader()
    return _loader


# Convenience functions for backwards compatibility with prerequisites.py
def get_course_info_from_catalog(major: str, course_code: str) -> Optional[Dict]:
    """Get course info from the catalog"""
    loader = get_catalog_loader()
    return loader.get_course_info(major, course_code)


def get_prerequisites_from_catalog(major: str, course_code: str) -> List[str]:
    """Get prerequisites from the catalog"""
    loader = get_catalog_loader()
    return loader.get_prerequisites(major, course_code)


if __name__ == "__main__":
    # Test the loader
    loader = CatalogLoader()
    print("Available majors:", loader.get_available_majors())
    print("\nCS Core Courses:")
    for course in loader.get_core_courses("Computer Science"):
        print(f"  - {course['course_code']}: {course['course_name']}")

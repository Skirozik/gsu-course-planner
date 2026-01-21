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
    """Loads and manages course catalogs for different majors and schools"""
    
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
        self.catalogs: Dict[str, Dict] = {}  # Format: {school_major: catalog_data}
        self.schools: set = set()  # Track available schools
        self.majors_by_school: Dict[str, List[str]] = {}  # Format: {school: [majors]}
        self.load_all_catalogs()
    
    def load_all_catalogs(self) -> None:
        """Load all JSON catalog files from the catalog directory"""
        if not self.catalog_dir.exists():
            print(f"Warning: Catalog directory not found: {self.catalog_dir}")
            return
        
        json_files = self.catalog_dir.glob("*.json")
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    catalog_data = json.load(f)
                    
                    # Extract school and major info
                    school = catalog_data.get("school", "Unknown")
                    major = catalog_data.get("major", json_file.stem)
                    
                    # Create composite key for lookup
                    composite_key = f"{school}_{major}"
                    self.catalogs[composite_key] = catalog_data
                    
                    # Track schools and majors
                    self.schools.add(school)
                    if school not in self.majors_by_school:
                        self.majors_by_school[school] = []
                    self.majors_by_school[school].append(major)
                    
                    print(f"[+] Loaded catalog: {school} - {major}")
            except json.JSONDecodeError as e:
                print(f"[!] Error loading {json_file}: {e}")
            except Exception as e:
                print(f"[!] Unexpected error loading {json_file}: {e}")
    
    def get_available_majors(self) -> List[str]:
        """Get list of available majors (for backward compatibility)"""
        return sorted(list(self.catalogs.keys()))
    
    def get_available_schools(self) -> List[str]:
        """Get list of available schools"""
        return sorted(list(self.schools))
    
    def get_majors_for_school(self, school: str) -> List[str]:
        """Get list of majors available for a specific school"""
        return sorted(self.majors_by_school.get(school, []))
    
    def get_catalog(self, school: str = None, major: str = None) -> Optional[Dict]:
        """
        Get the full catalog for a specific school and major
        
        Args:
            school: School name (e.g., "Georgia State University")
            major: Major name (e.g., "Computer Science")
        
        Returns:
            Catalog data or None if not found
        """
        if school and major:
            composite_key = f"{school}_{major}"
            return self.catalogs.get(composite_key)
        
        # For backward compatibility, accept composite key
        if major and "_" in major:
            return self.catalogs.get(major)
        
        # Try to find it if only major is provided
        if major:
            for key, catalog in self.catalogs.items():
                if catalog.get("major") == major:
                    return catalog
        
        return None
    
    def get_degree_requirements(self, school: str = None, major: str = None) -> Optional[Dict]:
        """Get degree requirements for a major"""
        catalog = self.get_catalog(school, major)
        if catalog:
            return catalog.get("degree_requirements", {})
        return None
    
    def get_core_courses(self, school: str = None, major: str = None) -> List[Dict]:
        """Get list of required core courses for a major"""
        catalog = self.get_catalog(school, major)
        if catalog:
            return catalog.get("core_requirements", {}).get("core", [])
        return []
    
    def get_elective_courses(self, school: str = None, major: str = None) -> List[Dict]:
        """Get list of elective courses for a major"""
        catalog = self.get_catalog(school, major)
        if catalog:
            return catalog.get("core_requirements", {}).get("electives", [])
        return []
    
    def get_math_requirements(self, school: str = None, major: str = None) -> List[Dict]:
        """Get list of math requirements for a major (backward compatibility)"""
        catalog = self.get_catalog(school, major)
        if catalog:
            return catalog.get("core_requirements", {}).get("math", [])
        return []
    
    def get_all_courses_for_major(self, school: str = None, major: str = None) -> Dict:
        """Get all courses (with prerequisites) for a major"""
        catalog = self.get_catalog(school, major)
        if catalog:
            return catalog.get("courses", {})
        return {}
    
    def get_course_info(self, school: str = None, major: str = None, course_code: str = None) -> Optional[Dict]:
        """Get detailed info for a specific course in a major's catalog"""
        if course_code is None:
            return None
        
        course_code = course_code.upper().strip()
        courses = self.get_all_courses_for_major(school, major)
        return courses.get(course_code)
    
    def get_prerequisites(self, school: str = None, major: str = None, course_code: str = None) -> List[str]:
        """Get prerequisites for a course in a specific major"""
        course = self.get_course_info(school, major, course_code)
        if course:
            return course.get("prerequisites", [])
        return []
    
    def get_corequisites(self, school: str = None, major: str = None, course_code: str = None) -> List[str]:
        """Get corequisites for a course in a specific major"""
        course = self.get_course_info(school, major, course_code)
        if course:
            return course.get("corequisites", [])
        return []
    
    def check_prerequisites_met(
        self, school: str = None, major: str = None, course_code: str = None, completed_courses: List[str] = None
    ) -> Dict:
        """
        Check if prerequisites are met for a course in a specific major
        
        Args:
            school: School/institution
            major: Major/degree program
            course_code: Code of the course to check
            completed_courses: List of completed course codes
        
        Returns:
            Dict with can_take (bool), met, missing prerequisites
        """
        if completed_courses is None:
            completed_courses = []
        
        course_code = course_code.upper().strip() if course_code else ""
        completed_upper = [c.upper().strip() for c in completed_courses]
        
        prereqs = self.get_prerequisites(school, major, course_code)
        met = [p for p in prereqs if p in completed_upper]
        missing = [p for p in prereqs if p not in completed_upper]
        
        return {
            "can_take": len(missing) == 0,
            "met": met,
            "missing": missing,
            "all_prerequisites": prereqs
        }
    
    def get_courses_unlocked_by(self, school: str = None, major: str = None, course_code: str = None) -> List[str]:
        """Get courses that have this course as a prerequisite in a major"""
        course_code = course_code.upper().strip() if course_code else ""
        unlocked = []
        courses = self.get_all_courses_for_major(school, major)
        
        for code, info in courses.items():
            if course_code in info.get("prerequisites", []):
                unlocked.append(code)
        
        return unlocked
    
    def get_all_prerequisites(
        self, school: str = None, major: str = None, course_code: str = None, visited: set = None
    ) -> List[str]:
        """
        Get all prerequisites recursively (the full prerequisite chain)
        Returns courses in order they should be taken
        """
        if visited is None:
            visited = set()
        
        course_code = course_code.upper().strip() if course_code else ""
        
        if course_code in visited:
            return []
        
        visited.add(course_code)
        all_prereqs = []
        
        direct_prereqs = self.get_prerequisites(school, major, course_code)
        for prereq in direct_prereqs:
            # Get prerequisites of prerequisites first
            deeper_prereqs = self.get_all_prerequisites(school, major, prereq, visited)
            for p in deeper_prereqs:
                if p not in all_prereqs:
                    all_prereqs.append(p)
            # Then add this prerequisite
            if prereq not in all_prereqs:
                all_prereqs.append(prereq)
        
        return all_prereqs
    
    def get_recommended_next_courses(
        self, school: str = None, major: str = None, completed_courses: List[str] = None, limit: int = 5
    ) -> List[Dict]:
        """
        Get recommended next courses a student can take
        
        Args:
            school: School/institution
            major: Student's major
            completed_courses: List of courses they've completed
            limit: Max number of recommendations to return
        
        Returns:
            List of courses they can now take, prioritized by prerequisites met
        """
        if completed_courses is None:
            completed_courses = []
            
        completed_upper = [c.upper().strip() for c in completed_courses]
        courses = self.get_all_courses_for_major(school, major)
        
        available = []
        
        for course_code, course_info in courses.items():
            # Skip if already taken
            if course_code in completed_upper:
                continue
            
            # Check if prerequisites are met
            prereqs_result = self.check_prerequisites_met(
                school, major, course_code, completed_courses
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
        self, school: str = None, major: str = None, completed_courses: List[str] = None
    ) -> Dict:
        """
        Calculate student's degree progress
        
        Args:
            school: School/institution
            major: Student's major
            completed_courses: List of completed course codes
        
        Returns:
            Dict with progress metrics
        """
        if completed_courses is None:
            completed_courses = []
            
        completed_upper = [c.upper().strip() for c in completed_courses]
        core_courses = self.get_core_courses(school, major)
        math_requirements = self.get_math_requirements(school, major)
        
        total_core = len(core_courses)
        completed_core = sum(1 for c in core_courses if c["course_code"] in completed_upper)
        
        total_math = len(math_requirements)
        completed_math = sum(1 for m in math_requirements if m["course_code"] in completed_upper)
        
        catalog = self.get_catalog(school, major)
        total_credits_required = catalog.get("metadata", {}).get("total_credits_required", 120) if catalog else 120
        
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

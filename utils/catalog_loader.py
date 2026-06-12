"""
Catalog Loader Module
Dynamically loads course catalogs from JSON files
Supports multiple majors and degree programs
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from utils.prerequisite_resolver import get_prerequisite_resolver

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
                with open(json_file, 'r', encoding='utf-8') as f:
                    catalog_data = json.load(f)

                    # Normalize divergent catalog shapes into a single internal
                    # structure (core_requirements.{core,electives,math}).
                    self._normalize_catalog(catalog_data)

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
    
    def _normalize_catalog(self, catalog: Dict) -> None:
        """
        Normalize a catalog in place so every catalog exposes
        ``core_requirements`` as ``{"core": [...], "electives": [...], "math": [...]}``
        where each entry is a course dict with ``course_code``/``course_name``/
        ``credits``/``description``.

        Handles two source shapes:
          - GSU catalogs: ``degree_requirements.{core_courses, electives, math_requirements}``
          - Georgia Tech: ``core_requirements.{Category: [course_code, ...]}`` (bare codes)
        """
        existing = catalog.get("core_requirements")

        # Already in the normalized shape — nothing to do.
        if isinstance(existing, dict) and any(
            k in existing for k in ("core", "electives", "math")
        ):
            return

        # GSU shape: lists of full course dicts under degree_requirements.
        deg_reqs = catalog.get("degree_requirements")
        if isinstance(deg_reqs, dict):
            catalog["core_requirements"] = {
                "core": deg_reqs.get("core_courses", []),
                "electives": deg_reqs.get("electives", []),
                "math": deg_reqs.get("math_requirements", []),
            }
            return

        # Georgia Tech shape: {Category: [course_code strings]}. Resolve each
        # bare code against the catalog's own ``courses`` map to build dicts.
        if isinstance(existing, dict):
            courses_map = catalog.get("courses", {})

            def to_course_dict(code: str) -> Dict:
                info = courses_map.get(code, {})
                return {
                    "course_code": code,
                    "course_name": info.get("name") or info.get("course_name") or code,
                    "credits": info.get("credits", 3),
                    "description": info.get("description", ""),
                }

            core, electives, math = [], [], []
            for category, codes in existing.items():
                if not isinstance(codes, list):
                    continue
                for code in codes:
                    if not isinstance(code, str):
                        continue
                    course_dict = to_course_dict(code)
                    if code.upper().startswith("MATH"):
                        math.append(course_dict)
                    elif "elective" in category.lower():
                        electives.append(course_dict)
                    else:
                        core.append(course_dict)

            catalog["core_requirements"] = {
                "core": core,
                "electives": electives,
                "math": math,
            }
            return

        # Unknown shape — guarantee the key exists so getters never KeyError.
        catalog.setdefault(
            "core_requirements", {"core": [], "electives": [], "math": []}
        )

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

        # Some catalog courses have an empty structured `prerequisites` list but a
        # populated free-text `prerequisites_raw`. Fall back to the text resolver
        # so we honor "X or Y" logic instead of treating them as having none.
        if not prereqs:
            course_info = self.get_course_info(school, major, course_code) or {}
            prereq_text = course_info.get("prerequisites_raw", "")
            if prereq_text:
                resolver = get_prerequisite_resolver()
                # No grades available on this path; assume completed courses passed.
                completed_dicts = [
                    {"course_code": c, "grade": "A"} for c in completed_courses
                ]
                result = resolver.evaluate_eligibility(prereq_text, completed_dicts)
                met = [str(r.course_code) for r in result.get("met_requirements", [])]
                missing = (
                    []
                    if result["eligible"]
                    else [str(r.course_code) for r in result.get("missing_requirements", [])]
                )
                return {
                    "can_take": result["eligible"],
                    "met": met,
                    "missing": missing,
                    "all_prerequisites": sorted(set(met + missing)),
                }

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

    def check_prerequisites_with_grades(
        self,
        school: str = None,
        major: str = None,
        course_code: str = None,
        completed_courses: List[Dict] = None,
        in_progress_courses: List[str] = None
    ) -> Dict:
        """
        Enhanced prerequisite checking using the prerequisite resolver.
        Evaluates eligibility based on actual prerequisite text and student grades.

        Args:
            school: School/institution
            major: Student's major
            course_code: Course to check eligibility for
            completed_courses: List of dicts with 'course_code' and 'grade' keys
            in_progress_courses: Optional list of currently enrolled course codes

        Returns:
            Dict with detailed eligibility information:
                - eligible (bool): Whether student can take the course
                - met_requirements (list): Prerequisites that are satisfied
                - missing_requirements (list): Prerequisites not satisfied
                - reason (str): Human-readable explanation
                - prerequisites_raw (str): Raw prerequisite text from catalog
        """
        if completed_courses is None:
            completed_courses = []
        if in_progress_courses is None:
            in_progress_courses = []

        course_code = course_code.upper().strip() if course_code else ""

        # Get course info from catalog
        courses = self.get_all_courses_for_major(school, major)
        if course_code not in courses:
            return {
                "eligible": False,
                "met_requirements": [],
                "missing_requirements": [],
                "reason": "Course not found in catalog",
                "prerequisites_raw": ""
            }

        course_info = courses[course_code]
        prereq_text = course_info.get("prerequisites_raw", "")

        # If no raw prerequisite text, fall back to simple check
        if not prereq_text:
            simple_result = self.check_prerequisites_met(school, major, course_code,
                                              [c['course_code'] for c in completed_courses])
            # Convert to new format
            return {
                "eligible": simple_result.get("can_take", False),
                "can_take": simple_result.get("can_take", False),
                "met_requirements": simple_result.get("met", []),
                "missing_requirements": simple_result.get("missing", []),
                "reason": "All prerequisites met" if simple_result.get("can_take") else f"Missing: {', '.join(simple_result.get('missing', []))}",
                "prerequisites_raw": ""
            }

        # Use prerequisite resolver for advanced evaluation
        resolver = get_prerequisite_resolver()
        result = resolver.evaluate_eligibility(prereq_text, completed_courses, in_progress_courses)

        # Add raw text to result
        result["prerequisites_raw"] = prereq_text
        result["can_take"] = result["eligible"]  # Alias for backwards compatibility

        return result

    def get_eligible_courses_with_grades(
        self,
        school: str = None,
        major: str = None,
        completed_courses: List[Dict] = None,
        in_progress_courses: List[str] = None,
        limit: int = None
    ) -> List[Dict]:
        """
        Get all courses a student is eligible to take, considering grades.

        Args:
            school: School/institution
            major: Student's major
            completed_courses: List of dicts with 'course_code' and 'grade'
            in_progress_courses: Optional list of currently enrolled courses
            limit: Optional max number of courses to return

        Returns:
            List of eligible courses with details
        """
        if completed_courses is None:
            completed_courses = []
        if in_progress_courses is None:
            in_progress_courses = []

        completed_codes = {c['course_code'].upper().strip() for c in completed_courses}
        in_progress_codes = {c.upper().strip() for c in in_progress_courses}
        all_taken = completed_codes | in_progress_codes

        courses = self.get_all_courses_for_major(school, major)
        eligible = []

        for course_code, course_info in courses.items():
            # Skip if already taken or in progress
            if course_code in all_taken:
                continue

            # Check eligibility
            result = self.check_prerequisites_with_grades(
                school, major, course_code, completed_courses, in_progress_courses
            )

            if result["eligible"]:
                eligible.append({
                    "course_code": course_code,
                    "course_name": course_info.get("name", ""),
                    "credits": course_info.get("credits", 3),
                    "description": course_info.get("description", ""),
                    "prerequisites_met": result["met_requirements"],
                    "eligibility_reason": result["reason"]
                })

        # Sort by course code
        eligible.sort(key=lambda x: x['course_code'])

        if limit:
            return eligible[:limit]
        return eligible


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
    """Get course info from the catalog (searches all schools by major name)"""
    loader = get_catalog_loader()
    return loader.get_course_info(major=major, course_code=course_code)


def get_prerequisites_from_catalog(major: str, course_code: str) -> List[str]:
    """Get prerequisites from the catalog (searches all schools by major name)"""
    loader = get_catalog_loader()
    return loader.get_prerequisites(major=major, course_code=course_code)


if __name__ == "__main__":
    # Test the loader
    loader = CatalogLoader()
    print("Available majors:", loader.get_available_majors())
    print("\nCS Core Courses:")
    for course in loader.get_core_courses("Georgia State University", "Computer Science"):
        print(f"  - {course['course_code']}: {course['course_name']}")

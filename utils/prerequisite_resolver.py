"""
Prerequisite Resolution Layer

Parses raw prerequisite text from course catalogs and evaluates student eligibility
based on completed courses and grades.

Features:
- Parses complex prerequisite text (AND/OR logic, grade requirements)
- Evaluates eligibility against student transcripts
- Provides detailed reasoning for ineligibility
- Handles corequisites and restrictions
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PrerequisiteRequirement:
    """Represents a single prerequisite requirement"""
    course_code: str
    min_grade: Optional[str] = "D"  # Default minimum grade

    def __repr__(self):
        if self.min_grade and self.min_grade != "D":
            return f"{self.course_code} (min grade: {self.min_grade})"
        return self.course_code


@dataclass
class PrerequisiteGroup:
    """Represents a group of prerequisites with AND/OR logic"""
    requirements: List[PrerequisiteRequirement]
    logic: str = "AND"  # "AND" or "OR"

    def __repr__(self):
        connector = " or " if self.logic == "OR" else " and "
        return connector.join(str(req) for req in self.requirements)


class PrerequisiteResolver:
    """
    Resolves prerequisite requirements by parsing raw text and evaluating
    against student transcripts.
    """

    # Grade hierarchy for comparison
    GRADE_VALUES = {
        'A+': 13, 'A': 12, 'A-': 11,
        'B+': 10, 'B': 9, 'B-': 8,
        'C+': 7, 'C': 6, 'C-': 5,
        'D+': 4, 'D': 3, 'D-': 2,
        'F': 1
    }

    def __init__(self):
        pass

    def parse_prerequisites(self, prereq_text: str) -> List[PrerequisiteGroup]:
        """
        Parse raw prerequisite text into structured format.

        Examples:
            "CSC 1301 with a C or higher"
            "(CSC 2720 or DSCI 2720) and either MATH 3020 or MATH 3030 with a C or higher"
            "CSC 2720, CSC 3210, and CSC 3320 with a C or higher"

        Args:
            prereq_text: Raw prerequisite text from catalog

        Returns:
            List of PrerequisiteGroup objects representing the parsed requirements
        """
        if not prereq_text or prereq_text.strip() == "":
            return []

        # Clean up text
        text = prereq_text.strip()

        # Extract grade requirement if present
        grade_match = re.search(r'with\s+(?:a\s+)?(?:grade\s+of\s+)?([A-DF][+-]?)\s+or\s+(?:higher|better)', text, re.IGNORECASE)
        min_grade = grade_match.group(1).upper() if grade_match else "D"

        # Remove grade requirement text for easier parsing
        text = re.sub(r'\s+with\s+(?:a\s+)?(?:grade\s+of\s+)?[A-DF][+-]?\s+or\s+(?:higher|better)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+with\s+[A-DF][+-]?\s+or\s+(?:higher|better)', '', text, flags=re.IGNORECASE)

        # Remove common suffixes
        text = re.sub(r'\.\s*Students must meet.*$', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+or permission of.*$', '', text, flags=re.IGNORECASE)

        groups = []

        # Handle parenthetical groups first: (CSC 2720 or DSCI 2720)
        paren_pattern = r'\(([^)]+)\)'
        paren_matches = list(re.finditer(paren_pattern, text))

        if paren_matches:
            # Process text with parenthetical groups
            for match in paren_matches:
                group_text = match.group(1)
                group = self._parse_course_group(group_text, min_grade)
                if group:
                    groups.append(group)

            # Remove parenthetical content and process remaining text
            remaining_text = re.sub(paren_pattern, '', text)
            remaining_text = re.sub(r'\s+and\s+', ' ', remaining_text, flags=re.IGNORECASE)
            remaining_text = remaining_text.strip()

            if remaining_text:
                # Process remaining courses
                remaining_group = self._parse_course_group(remaining_text, min_grade)
                if remaining_group:
                    groups.append(remaining_group)
        else:
            # No parenthetical groups - parse entire text
            group = self._parse_course_group(text, min_grade)
            if group:
                groups.append(group)

        return groups

    def _parse_course_group(self, text: str, default_min_grade: str = "D") -> Optional[PrerequisiteGroup]:
        """
        Parse a single group of courses (no nested parentheses).

        Determines if group uses OR or AND logic.
        """
        if not text.strip():
            return None

        # Detect logic type
        has_or = bool(re.search(r'\s+or\s+', text, re.IGNORECASE))
        logic = "OR" if has_or else "AND"

        # Extract all course codes
        # Pattern: DEPT #### or DEPT ####L (lab courses)
        course_pattern = r'\b([A-Z]{2,4})\s+(\d{4}[A-Z]?)\b'
        matches = re.findall(course_pattern, text)

        requirements = []
        for dept, number in matches:
            course_code = f"{dept} {number}"
            requirements.append(PrerequisiteRequirement(
                course_code=course_code,
                min_grade=default_min_grade
            ))

        if not requirements:
            return None

        return PrerequisiteGroup(requirements=requirements, logic=logic)

    def evaluate_eligibility(
        self,
        prereq_text: str,
        completed_courses: List[Dict],
        in_progress_courses: List[str] = None
    ) -> Dict:
        """
        Evaluate if student meets prerequisites.

        Args:
            prereq_text: Raw prerequisite text from catalog
            completed_courses: List of dicts with 'course_code' and 'grade' keys
            in_progress_courses: Optional list of currently enrolled course codes

        Returns:
            Dict with:
                - eligible (bool): Whether student can take the course
                - met_requirements (list): Requirements that are satisfied
                - missing_requirements (list): Requirements not satisfied
                - reason (str): Human-readable explanation
        """
        if in_progress_courses is None:
            in_progress_courses = []

        # Parse prerequisites
        groups = self.parse_prerequisites(prereq_text)

        if not groups:
            return {
                "eligible": True,
                "met_requirements": [],
                "missing_requirements": [],
                "reason": "No prerequisites required"
            }

        # Build student transcript lookup
        transcript = {}
        for course in completed_courses:
            code = course.get('course_code', '').upper().strip()
            grade = course.get('grade', 'F').upper()
            transcript[code] = grade

        # Evaluate each group
        all_met = []
        all_missing = []
        group_results = []

        for group in groups:
            group_met, group_missing = self._evaluate_group(group, transcript, in_progress_courses)
            all_met.extend(group_met)
            all_missing.extend(group_missing)

            # For AND groups, all requirements must be met
            # For OR groups, at least one requirement must be met
            if group.logic == "AND":
                group_satisfied = len(group_missing) == 0
            else:  # OR
                group_satisfied = len(group_met) > 0

            group_results.append(group_satisfied)

        # All groups must be satisfied (groups are implicitly ANDed together)
        eligible = all(group_results)

        # Build reason
        if eligible:
            reason = "All prerequisites met"
        else:
            missing_str = ", ".join(str(req) for req in all_missing)
            reason = f"Missing: {missing_str}"

        return {
            "eligible": eligible,
            "met_requirements": all_met,
            "missing_requirements": all_missing,
            "reason": reason,
            "prerequisite_groups": groups
        }

    def _evaluate_group(
        self,
        group: PrerequisiteGroup,
        transcript: Dict[str, str],
        in_progress: List[str]
    ) -> Tuple[List[PrerequisiteRequirement], List[PrerequisiteRequirement]]:
        """
        Evaluate a single prerequisite group.

        Returns:
            Tuple of (met_requirements, missing_requirements)
        """
        met = []
        missing = []

        for req in group.requirements:
            course_code = req.course_code.upper().strip()

            # Check if completed
            if course_code in transcript:
                grade = transcript[course_code]

                # Check if grade meets minimum requirement
                if self._meets_grade_requirement(grade, req.min_grade):
                    met.append(req)
                else:
                    # Completed but grade too low
                    missing.append(req)
            elif course_code in [c.upper().strip() for c in in_progress]:
                # Currently taking - counts as not met (can't use as prereq yet)
                missing.append(req)
            else:
                # Not taken at all
                missing.append(req)

        return met, missing

    def _meets_grade_requirement(self, earned_grade: str, required_grade: str) -> bool:
        """
        Check if earned grade meets or exceeds required grade.

        Args:
            earned_grade: Grade student earned (e.g., "B+")
            required_grade: Minimum required grade (e.g., "C")

        Returns:
            True if earned grade meets requirement
        """
        earned_value = self.GRADE_VALUES.get(earned_grade.upper(), 0)
        required_value = self.GRADE_VALUES.get(required_grade.upper(), 0)

        return earned_value >= required_value

    def format_prerequisites(self, prereq_text: str) -> str:
        """
        Format raw prerequisite text into human-readable format.

        Args:
            prereq_text: Raw prerequisite text

        Returns:
            Formatted, readable prerequisite description
        """
        if not prereq_text or prereq_text.strip() == "":
            return "None"

        groups = self.parse_prerequisites(prereq_text)

        if not groups:
            return "None"

        formatted_groups = []
        for group in groups:
            formatted_groups.append(str(group))

        return " AND ".join(formatted_groups)

    def get_missing_prerequisites_detail(
        self,
        course_code: str,
        prereq_text: str,
        completed_courses: List[Dict],
        catalog_loader
    ) -> Dict:
        """
        Get detailed information about missing prerequisites including
        prerequisites of prerequisites.

        Args:
            course_code: Course to check
            prereq_text: Raw prerequisite text
            completed_courses: Student's completed courses
            catalog_loader: CatalogLoader instance for recursive prerequisite lookup

        Returns:
            Dict with detailed missing prerequisite information
        """
        result = self.evaluate_eligibility(prereq_text, completed_courses)

        if result["eligible"]:
            return {
                "can_take_now": True,
                "missing_direct": [],
                "missing_chain": []
            }

        # Get prerequisites of missing prerequisites
        missing_chain = []
        completed_codes = {c['course_code'].upper().strip() for c in completed_courses}

        for missing_req in result["missing_requirements"]:
            missing_code = missing_req.course_code

            # Get prerequisites of this missing course
            # This would require integration with catalog_loader
            # For now, return basic info
            missing_chain.append({
                "course_code": missing_code,
                "min_grade": missing_req.min_grade,
                "sub_prerequisites": []  # Would be populated recursively
            })

        return {
            "can_take_now": False,
            "missing_direct": [str(req) for req in result["missing_requirements"]],
            "missing_chain": missing_chain,
            "reason": result["reason"]
        }


# Global resolver instance
_resolver = None

def get_prerequisite_resolver() -> PrerequisiteResolver:
    """Get singleton PrerequisiteResolver instance"""
    global _resolver
    if _resolver is None:
        _resolver = PrerequisiteResolver()
    return _resolver


# Convenience functions
def check_course_eligibility(
    prereq_text: str,
    completed_courses: List[Dict],
    in_progress_courses: List[str] = None
) -> Dict:
    """
    Convenience function to check if student can take a course.

    Args:
        prereq_text: Raw prerequisite text from catalog
        completed_courses: List of dicts with 'course_code' and 'grade'
        in_progress_courses: Optional list of currently enrolled courses

    Returns:
        Eligibility result dict
    """
    resolver = get_prerequisite_resolver()
    return resolver.evaluate_eligibility(prereq_text, completed_courses, in_progress_courses)


def format_prerequisites_readable(prereq_text: str) -> str:
    """
    Format prerequisite text in human-readable format.

    Args:
        prereq_text: Raw prerequisite text

    Returns:
        Formatted string
    """
    resolver = get_prerequisite_resolver()
    return resolver.format_prerequisites(prereq_text)

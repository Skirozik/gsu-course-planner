"""
Academic Evaluation Parser
Extracts course requirements and progress from GSU academic evaluation PDFs
"""

import PyPDF2
import re
from typing import Dict, List, Optional
from io import BytesIO


def parse_academic_eval(file_content: bytes) -> Dict:
    """
    Parse GSU academic evaluation PDF and extract all relevant information

    Args:
        file_content: Raw PDF file content as bytes

    Returns:
        Dictionary containing:
        - student_info: name, id, gpa, major, credits
        - completed_courses: List of completed courses with grades
        - in_progress_courses: List of currently enrolled courses
        - required_courses: List of courses still needed
        - requirements_summary: Overview of degree requirements
    """

    # Extract text from PDF
    text = extract_pdf_text(file_content)

    # Parse different sections
    student_info = parse_student_info(text)
    completed_courses = parse_completed_courses(text)
    in_progress_courses = parse_in_progress_courses(text)
    required_courses = parse_required_courses(text)
    requirements_summary = parse_requirements_summary(text)

    return {
        "student_info": student_info,
        "completed_courses": completed_courses,
        "in_progress_courses": in_progress_courses,
        "required_courses": required_courses,
        "requirements_summary": requirements_summary,
        "raw_text": text  # Keep for debugging
    }


def extract_pdf_text(pdf_content: bytes) -> str:
    """Extract all text from PDF"""
    try:
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""


def parse_student_info(text: str) -> Dict:
    """Extract student information from the evaluation"""
    info = {
        "student_name": "",
        "student_id": "",
        "gpa": 0.0,
        "major": "",
        "college": "",
        "degree": "",
        "credits_required": 120,
        "credits_applied": 0,
        "catalog_year": "",
        "academic_standing": "",
        "advisor": ""
    }

    # Student name - appears at top
    name_match = re.search(r'Student name\s+([A-Za-z]+,\s*[A-Za-z]+)', text)
    if name_match:
        info["student_name"] = name_match.group(1).strip()

    # Student ID
    id_match = re.search(r'Student ID\s+\*+(\d+)', text)
    if id_match:
        info["student_id"] = id_match.group(1)

    # GPA - look for "GSU GPA" followed by number
    gpa_match = re.search(r'GSU GPA\s+(\d+\.\d+)', text)
    if gpa_match:
        info["gpa"] = float(gpa_match.group(1))

    # Major/Pathway
    major_match = re.search(r'Majors/Pathway\s+([A-Za-z\-\s]+?)(?=College|$)', text)
    if major_match:
        info["major"] = major_match.group(1).strip()

    # College
    college_match = re.search(r'College\s+(College of [A-Za-z\s&]+?)(?=Degree|$)', text)
    if college_match:
        info["college"] = college_match.group(1).strip()

    # Credits required and applied
    credits_match = re.search(r'Credits required:\s*(\d+)\s*Credits applied:\s*(\d+)', text)
    if credits_match:
        info["credits_required"] = int(credits_match.group(1))
        info["credits_applied"] = int(credits_match.group(2))

    # Catalog year
    catalog_match = re.search(r'Catalog year:\s*(\d{4}-\d{4})', text)
    if catalog_match:
        info["catalog_year"] = catalog_match.group(1)

    # Academic standing
    standing_match = re.search(r'Academic Standing\s+([A-Za-z\s]+?)(?=Department|$)', text)
    if standing_match:
        info["academic_standing"] = standing_match.group(1).strip()

    # Advisor
    advisor_match = re.search(r'Advisor\s+([A-Za-z]+,\s*[A-Za-z]+)', text)
    if advisor_match:
        info["advisor"] = advisor_match.group(1).strip()

    return info


def parse_completed_courses(text: str) -> List[Dict]:
    """Extract completed courses with grades"""
    completed = []

    # Pattern for course entries: DEPT #### COURSE NAME GRADE CREDITS TERM
    # Example: CSC 1301 PRINCIPLES OF COMPUTER SCI I B 4 Fall Semester 2023
    course_pattern = re.compile(
        r'([A-Z]{2,4})\s+(\d{4}[A-Z]?)\s+'  # Course code (e.g., CSC 1301, BIOL 1103L)
        r'([A-Z][A-Z\s&\-:]+?)\s+'           # Course name
        r'([A-DF][+-]?|W|NA)\s+'             # Grade
        r'\(?(\d+)\)?\s+'                     # Credits (may be in parentheses for in-progress)
        r'((?:Fall|Spring|Summer)\s+Semester\s+\d{4})',  # Term
        re.IGNORECASE
    )

    for match in course_pattern.finditer(text):
        dept = match.group(1).upper()
        number = match.group(2)
        name = match.group(3).strip()
        grade = match.group(4).upper()
        credits = int(match.group(5))
        term = match.group(6)

        # Skip if grade is NA (in-progress) or W (withdrawn)
        if grade not in ['NA', 'W', '-W']:
            completed.append({
                "course_code": f"{dept} {number}",
                "course_name": name,
                "grade": grade,
                "credits": credits,
                "term": term
            })

    # Remove duplicates (keep the one with better grade if retaken)
    unique_courses = {}
    grade_order = {'A+': 13, 'A': 12, 'A-': 11, 'B+': 10, 'B': 9, 'B-': 8,
                   'C+': 7, 'C': 6, 'C-': 5, 'D+': 4, 'D': 3, 'D-': 2, 'F': 1}

    for course in completed:
        code = course["course_code"]
        if code not in unique_courses:
            unique_courses[code] = course
        else:
            # Keep the better grade
            current_grade = unique_courses[code]["grade"]
            new_grade = course["grade"]
            if grade_order.get(new_grade, 0) > grade_order.get(current_grade, 0):
                unique_courses[code] = course

    return list(unique_courses.values())


def parse_in_progress_courses(text: str) -> List[Dict]:
    """Extract currently enrolled (in-progress) courses"""
    in_progress = []

    # Look for the "In-progress" section
    in_progress_section = re.search(r'In-progress.*?(?=Not Counted|Legend|$)', text, re.DOTALL)

    if in_progress_section:
        section_text = in_progress_section.group(0)

        # Pattern for in-progress courses (grade is NA, credits in parentheses)
        course_pattern = re.compile(
            r'([A-Z]{2,4})\s+(\d{4}[A-Z]?)\s+'
            r'([A-Z][A-Z\s&\-:]+?)\s+'
            r'NA\s+'
            r'\((\d+)\)\s+'
            r'((?:Fall|Spring|Summer)\s+Semester\s+\d{4})',
            re.IGNORECASE
        )

        for match in course_pattern.finditer(section_text):
            in_progress.append({
                "course_code": f"{match.group(1).upper()} {match.group(2)}",
                "course_name": match.group(3).strip(),
                "credits": int(match.group(4)),
                "term": match.group(5)
            })

    return in_progress


def parse_required_courses(text: str) -> List[Dict]:
    """Extract courses still needed for degree completion"""
    required = []

    # Pattern for "Still needed" requirements
    # Example: Still needed: 4 Credits in CSC 3350
    still_needed_pattern = re.compile(
        r'Still needed:\s*(\d+)\s*Credits?\s+in\s+([A-Z]{2,4}\s+\d{4}[A-Z]?(?:\s+or\s+\d{4})?)',
        re.IGNORECASE
    )

    for match in still_needed_pattern.finditer(text):
        credits = int(match.group(1))
        courses_str = match.group(2)

        # Handle "or" options (e.g., "CSC 4320 or 4330")
        if ' or ' in courses_str.lower():
            parts = re.split(r'\s+or\s+', courses_str, flags=re.IGNORECASE)
            base_dept = re.match(r'([A-Z]{2,4})', parts[0]).group(1)

            options = []
            for part in parts:
                if re.match(r'[A-Z]{2,4}\s+\d{4}', part):
                    options.append(part.strip())
                else:
                    # Just a number, use base department
                    options.append(f"{base_dept} {part.strip()}")

            required.append({
                "credits": credits,
                "courses": options,
                "is_choice": True,
                "requirement_type": "major"
            })
        else:
            required.append({
                "credits": credits,
                "courses": [courses_str.strip()],
                "is_choice": False,
                "requirement_type": "major"
            })

    # Pattern for elective requirements
    # Example: 16 Credits in CSC 3@ or 4@ Except CSC 4870...
    elective_pattern = re.compile(
        r'Still needed:\s*(\d+)\s*Credits?\s+in\s+([A-Z@\s\d]+?)(?:\s+Except\s+(.+?))?(?=Still needed|$)',
        re.IGNORECASE
    )

    for match in elective_pattern.finditer(text):
        credits = int(match.group(1))
        course_spec = match.group(2).strip()
        exceptions = match.group(3).strip() if match.group(3) else ""

        # Check if this is an elective pattern (contains @)
        if '@' in course_spec:
            required.append({
                "credits": credits,
                "courses": [course_spec],
                "exceptions": exceptions,
                "is_choice": True,
                "is_elective": True,
                "requirement_type": "elective"
            })

    return required


def parse_requirements_summary(text: str) -> Dict:
    """Extract high-level requirements status"""
    summary = {
        "degree_name": "",
        "total_credits_required": 120,
        "total_credits_completed": 0,
        "core_curriculum_complete": False,
        "major_requirements_complete": False,
        "field_of_study_complete": False,
        "residency_requirement_complete": False,
        "sections": []
    }

    # Degree name
    degree_match = re.search(r'BS in ([A-Za-z\-\s]+?)(?:\s+INCOMPLETE|\s+COMPLETE)', text)
    if degree_match:
        summary["degree_name"] = f"BS in {degree_match.group(1).strip()}"

    # Check completion status of major sections
    if 'CAS IMPACTS Core Curriculum COMPLETE' in text:
        summary["core_curriculum_complete"] = True

    if 'Major - Pre-Computer Science COMPLETE' in text or 'Major - Computer Science COMPLETE' in text:
        summary["major_requirements_complete"] = True

    if 'Field of Study - Pre-Computer Science COMPLETE' in text:
        summary["field_of_study_complete"] = True

    if 'Residency Requirement - CAS COMPLETE' in text:
        summary["residency_requirement_complete"] = True

    # Extract section statuses
    section_pattern = re.compile(
        r'([\w\s\-]+?)\s+(COMPLETE|INCOMPLETE|IN-PROGRESS|SEE ADVISOR)',
        re.IGNORECASE
    )

    for match in section_pattern.finditer(text):
        section_name = match.group(1).strip()
        status = match.group(2).upper()

        # Filter out noise
        if len(section_name) > 5 and section_name not in ['Georgia State University']:
            summary["sections"].append({
                "name": section_name,
                "status": status
            })

    return summary


def get_next_semester_recommendations(eval_data: Dict) -> Dict:
    """
    Analyze the evaluation data and recommend courses for next semester

    Args:
        eval_data: Parsed academic evaluation data

    Returns:
        Dictionary with recommended courses and reasoning
    """
    completed_codes = [c["course_code"] for c in eval_data["completed_courses"]]
    in_progress_codes = [c["course_code"] for c in eval_data["in_progress_courses"]]
    all_taken = completed_codes + in_progress_codes

    recommendations = {
        "available_courses": [],
        "prerequisites_met": [],
        "prerequisites_needed": []
    }

    # Define prerequisite chains for CS courses
    prerequisites = {
        "CSC 2720": ["CSC 1302"],  # Data Structures requires CS II
        "CSC 3210": ["CSC 2720"],  # Computer Org requires Data Structures
        "CSC 3320": ["CSC 2720"],  # System Level Programming requires Data Structures
        "CSC 3350": ["CSC 2720"],  # Software Development requires Data Structures
        "CSC 4320": ["CSC 3320"],  # Operating Systems requires System Level
        "CSC 4330": ["CSC 3320"],  # Programming Languages requires System Level
        "CSC 4351": ["CSC 3350"],  # Capstone I requires Software Dev
        "CSC 4352": ["CSC 4351"],  # Capstone II requires Capstone I
        "CSC 4520": ["CSC 2720", "MATH 2420"],  # Algorithms requires DS and Discrete Math
        "MATH 2212": ["MATH 2211"],  # Calc II requires Calc I
        "MATH 2641": ["MATH 2211"],  # Linear Algebra requires Calc I
        "MATH 3020": ["MATH 2211"],  # Prob & Stats requires Calc I
    }

    for req in eval_data["required_courses"]:
        for course in req["courses"]:
            # Clean up course code
            course_code = course.strip().upper()

            # Skip if already taken or in progress
            if course_code in all_taken:
                continue

            # Skip elective patterns
            if '@' in course_code:
                continue

            # Check prerequisites
            prereqs = prerequisites.get(course_code, [])
            prereqs_met = all(p in all_taken for p in prereqs)

            course_info = {
                "course_code": course_code,
                "credits": req["credits"],
                "prerequisites": prereqs,
                "prerequisites_met": prereqs_met
            }

            if prereqs_met:
                recommendations["available_courses"].append(course_info)
                recommendations["prerequisites_met"].append(course_code)
            else:
                missing = [p for p in prereqs if p not in all_taken]
                course_info["missing_prerequisites"] = missing
                recommendations["prerequisites_needed"].append(course_info)

    return recommendations


# Example usage
if __name__ == "__main__":
    # Test with a sample file
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1], 'rb') as f:
            content = f.read()

        result = parse_academic_eval(content)

        print("=== Student Info ===")
        for key, value in result["student_info"].items():
            print(f"{key}: {value}")

        print("\n=== Completed Courses ===")
        for course in result["completed_courses"][:10]:
            print(f"{course['course_code']}: {course['course_name']} ({course['grade']})")

        print("\n=== In Progress ===")
        for course in result["in_progress_courses"]:
            print(f"{course['course_code']}: {course['course_name']}")

        print("\n=== Still Needed ===")
        for req in result["required_courses"]:
            print(f"{req['credits']} credits: {req['courses']}")

        print("\n=== Recommendations ===")
        recs = get_next_semester_recommendations(result)
        for course in recs["available_courses"]:
            print(f"Can take: {course['course_code']} ({course['credits']} credits)")

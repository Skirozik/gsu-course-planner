"""
Georgia Tech DegreeWorks Parser

Parses Georgia Tech DegreeWorks PDF academic evaluations.
Different format from GSU, so requires separate parser.
"""

import PyPDF2
import re
from typing import Dict, List, Optional
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def parse_gatech_degreeworks(pdf_content: bytes) -> Dict:
    """
    Parse Georgia Tech DegreeWorks PDF

    Args:
        pdf_content: PDF file content as bytes

    Returns:
        Dict with student info, completed courses, in-progress courses, required courses
    """
    try:
        # Open PDF from bytes using PyPDF2
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Extract all text
        full_text = ""
        for page in pdf_reader.pages:
            full_text += page.extract_text()

        pdf_file.close()

        # Parse student information
        student_info = _extract_student_info(full_text)

        # Parse courses
        completed_courses = _extract_completed_courses(full_text)
        in_progress_courses = _extract_in_progress_courses(full_text)
        required_courses = _extract_required_courses(full_text)

        result = {
            "student_info": student_info,
            "completed_courses": completed_courses,
            "in_progress_courses": in_progress_courses,
            "required_courses": required_courses,
            "requirements_summary": _generate_requirements_summary(
                student_info, required_courses
            )
        }

        return result

    except Exception as e:
        logger.error(f"Error parsing Georgia Tech DegreeWorks: {e}")
        raise


def _extract_student_info(text: str) -> Dict:
    """Extract student information from PDF text"""
    info = {
        "student_name": "",
        "student_id": "",
        "major": "",
        "gpa": 0.0,
        "credits_applied": 0,
        "credits_required": 0,
        "school": "Georgia Tech",
        "degree": "",
        "concentration": "",
        "college": ""
    }

    # Extract student name (format: "Vo, Nhi N - 903878789" at top)
    name_match = re.search(r'Georgia Tech\s*([^\d]+?)\s*-\s*(\d{9})', text)
    if name_match:
        info["student_name"] = name_match.group(1).strip()
        info["student_id"] = name_match.group(2).strip()

    # Alternative: Look for "Student name" field
    if not info["student_name"]:
        name_match = re.search(r'Student name\s+([A-Z][a-z]+,\s+[A-Z][a-z]+(?:\s+[A-Z])?)', text)
        if name_match:
            info["student_name"] = name_match.group(1).strip()

    # Alternative student ID
    if not info["student_id"]:
        id_match = re.search(r'Student ID\s+(\d{9})', text)
        if id_match:
            info["student_id"] = id_match.group(1).strip()

    # Extract degree
    degree_match = re.search(r'Degree\s*(BS in [A-Za-z\s]+?)(?:Audit|Program|Major|$)', text)
    if degree_match:
        info["degree"] = degree_match.group(1).strip()

    # Extract major (look for "Major Computer Science" or similar)
    major_match = re.search(r'Major\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+Program', text)
    if major_match:
        info["major"] = major_match.group(1).strip()

    # Extract concentration (format: "Concentration BSCS: Media-People")
    concentration_match = re.search(r'Concentration\s+(BSCS:[^\n]+?)(?=\s*Program|Major|College|Degree|$)', text)
    if concentration_match:
        info["concentration"] = concentration_match.group(1).strip()

    # Extract college
    college_match = re.search(r'College\s+(College of [A-Za-z\s]+?)(?=\s*BSCS|Program|Major|Degree|Concentration|$)', text)
    if college_match:
        info["college"] = college_match.group(1).strip()

    # Extract GPA (first occurrence)
    gpa_match = re.search(r'GPA:\s*([\d.]+)', text)
    if gpa_match:
        try:
            info["gpa"] = float(gpa_match.group(1))
        except ValueError:
            info["gpa"] = 0.0

    # Extract credits (format: "Credits required: 126Credits applied:  89" - note spacing)
    credits_match = re.search(r'Credits required:\s*(\d+)\s*Credits applied:\s*(\d+)', text)
    if credits_match:
        try:
            info["credits_required"] = int(credits_match.group(1))
            info["credits_applied"] = int(credits_match.group(2))
        except ValueError:
            pass

    return info


def _extract_completed_courses(text: str) -> List[Dict]:
    """
    Extract completed courses (courses with grades A, B, C, D, F, or T for transfer)
    Format in PDF: COURSE CODE + Title + Grade + Credits + Term (no line breaks)
    Example: "ENGL 1101English Composition IA 3Fall 2023"
    """
    completed = []

    # Pattern to match course entries
    # Looks for: DEPT NUMTitle Grade Credits Term
    # The trick is the title starts immediately after the course number (no space)
    pattern = r'([A-Z]{2,4})\s+(\d{4}[A-Z]?)([A-Z][a-z][A-Za-z\s&\-:,()]+?)([A-F][+-]?|T)\s+(\d+)\s*(Fall|Spring|Summer)\s+(\d{4})'

    for match in re.finditer(pattern, text):
        dept = match.group(1)
        number = match.group(2)
        title = match.group(3).strip()
        grade = match.group(4)
        credits = int(match.group(5))
        semester = match.group(6)
        year = match.group(7)
        term = f"{semester} {year}"

        # Skip if grade is IP (in progress) or W (withdrawn)
        if grade in ['IP', 'W']:
            continue

        # Clean up title (remove trailing single letters that might be part of grade)
        title = re.sub(r'\s+[A-F]$', '', title)

        completed.append({
            "course_code": f"{dept} {number}",
            "course_name": title,
            "grade": grade,
            "credits": credits,
            "term": term
        })

    return completed


def _extract_in_progress_courses(text: str) -> List[Dict]:
    """
    Extract in-progress courses (marked as IP)
    Format: COURSE CODECourse TitleIP (Credits) Term Year
    Example: "MATH 1554Linear AlgebraIP (4)Spring 2026"
    """
    in_progress = []
    seen = set()  # Track duplicates

    # Pattern to match in-progress courses
    # Example: CS 1332Data Struct & AlgorithmsIP (3)Spring 2026
    pattern = r'([A-Z]{2,4})\s+(\d{4}[A-Z]?)([A-Z][a-z][A-Za-z\s&\-:,()]+?)IP\s+\((\d+)\)\s*(Fall|Spring|Summer)\s+(\d{4})'

    for match in re.finditer(pattern, text):
        dept = match.group(1)
        number = match.group(2)
        title = match.group(3).strip()
        credits = int(match.group(4))
        semester = match.group(5)
        year = match.group(6)
        term = f"{semester} {year}"

        course_code = f"{dept} {number}"

        # Skip duplicates
        if course_code in seen:
            continue
        seen.add(course_code)

        in_progress.append({
            "course_code": course_code,
            "course_name": title,
            "credits": credits,
            "term": term
        })

    return in_progress


def _extract_required_courses(text: str) -> List[Dict]:
    """
    Extract required courses that still need to be completed
    Parse "Still needed" lines
    Format: "Still needed:1 Class in CS 2340" (no line breaks)
    """
    required = []

    # Pattern 1: Simple requirements like "Still needed:1 Class in CS 1100"
    # This matches: Still needed:N Class(es) in DEPT NUM
    simple_pattern = r'Still needed:(\d+)\s+Class(?:es)?\s+in\s+([A-Z]{2,5})\s+(\d{4})'

    for match in re.finditer(simple_pattern, text):
        num_classes = int(match.group(1))
        dept = match.group(2)
        course_num = match.group(3)

        required.append({
            "courses": [f"{dept} {course_num}"],
            "credits": num_classes * 3,  # Assume 3 credits per class
            "is_choice": False,
            "is_elective": False
        })

    # Pattern 2: Multiple choice requirements like "Still needed:1 Class in CS 2050 or 2051"
    # This matches: Still needed:N Class(es) in DEPT NUM or NUM or NUM
    choice_pattern = r'Still needed:(\d+)\s+Class(?:es)?\s+in\s+([A-Z]{2,5})\s+(\d{4}(?:\s+or\s+\d{4})+)'

    for match in re.finditer(choice_pattern, text):
        num_classes = int(match.group(1))
        dept = match.group(2)
        numbers_text = match.group(3)

        # Extract all course numbers
        numbers = re.findall(r'\d{4}', numbers_text)
        course_codes = [f"{dept} {num}" for num in numbers]

        required.append({
            "courses": course_codes,
            "credits": num_classes * 3,
            "is_choice": True,
            "is_elective": False
        })

    # Pattern 3: Complex multi-course requirements like "3 Classes in CS 3451 or 4455 or 4460"
    # Where only first course has dept prefix
    multi_pattern = r'Still needed:(\d+)\s+Classes\s+in\s+([A-Z]{2,5})\s+(\d{4}(?:\s+or\s+\d{4})+)'

    for match in re.finditer(multi_pattern, text):
        num_classes = int(match.group(1))
        dept = match.group(2)
        numbers_text = match.group(3)

        # Extract all course numbers
        numbers = re.findall(r'\d{4}', numbers_text)
        course_codes = [f"{dept} {num}" for num in numbers]

        required.append({
            "courses": course_codes,
            "credits": num_classes * 3,
            "is_choice": True,
            "is_elective": True  # Multiple classes to choose = elective
        })

    return required


def _generate_requirements_summary(student_info: Dict, required_courses: List[Dict]) -> Dict:
    """Generate a summary of requirements"""
    total_credits_needed = student_info["credits_required"] - student_info["credits_applied"]

    return {
        "total_credits_needed": total_credits_needed,
        "core_requirements_met": total_credits_needed < 40,  # Rough estimate
        "major_requirements_remaining": len(required_courses),
        "estimated_semesters_remaining": max(1, total_credits_needed // 15)
    }


# Test function
if __name__ == "__main__":
    # Test with Nhi's PDF
    test_pdf_path = "/Users/zekeyeagar/Documents/gsu-course-planner-master/Nhi academic eval.pdf"

    with open(test_pdf_path, "rb") as f:
        pdf_content = f.read()

    result = parse_gatech_degreeworks(pdf_content)

    print("=" * 70)
    print("GEORGIA TECH DEGREEWORKS PARSER TEST")
    print("=" * 70)

    print("\n📋 Student Info:")
    for key, value in result["student_info"].items():
        print(f"  {key}: {value}")

    print(f"\n✅ Completed Courses ({len(result['completed_courses'])}):")
    for course in result["completed_courses"][:5]:
        print(f"  {course['course_code']} - {course['course_name']} ({course['grade']}, {course['credits']} credits, {course['term']})")

    print(f"\n📚 In-Progress Courses ({len(result['in_progress_courses'])}):")
    for course in result["in_progress_courses"]:
        print(f"  {course['course_code']} - {course['course_name']} ({course['credits']} credits, {course['term']})")

    print(f"\n📝 Required Courses ({len(result['required_courses'])}):")
    for req in result["required_courses"][:5]:
        print(f"  {req['courses']} ({req['credits']} credits)")

    print("\n" + "=" * 70)

"""
Georgia Tech DegreeWorks Parser

Parses Georgia Tech DegreeWorks PDF academic evaluations.
Different format from GSU, so requires separate parser.
"""

import re
from typing import Dict, List, Optional
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def _extract_text(pdf_content: bytes) -> str:
    """Extract text from PDF using pdfplumber with PyPDF2 fallback."""
    # Try pdfplumber first — handles modern PDFs better
    try:
        import pdfplumber
        with pdfplumber.open(BytesIO(pdf_content)) as pdf:
            pages = [p.extract_text() or "" for p in pdf.pages]
            text = "\n".join(pages)
            if text.strip():
                return text
    except Exception as e:
        logger.warning(f"pdfplumber failed, falling back to PyPDF2: {e}")

    # Fallback to PyPDF2
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(BytesIO(pdf_content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        logger.error(f"PyPDF2 also failed: {e}")
        raise ValueError(f"Could not extract text from PDF: {e}")


def parse_gatech_degreeworks(pdf_content: bytes) -> Dict:
    """
    Parse Georgia Tech DegreeWorks PDF.
    Returns a valid structure even when regex finds nothing — never raises on
    partial parse so the frontend can still proceed with whatever data we got.
    """
    full_text = _extract_text(pdf_content)

    if not full_text.strip():
        raise ValueError("PDF appears to be empty or image-only (no extractable text).")

    student_info = _extract_student_info(full_text)
    completed_courses = _extract_completed_courses(full_text)
    in_progress_courses = _extract_in_progress_courses(full_text)
    required_courses = _extract_required_courses(full_text)

    logger.info(
        f"GT parse: {len(completed_courses)} completed, "
        f"{len(in_progress_courses)} in-progress, "
        f"{len(required_courses)} requirements"
    )

    return {
        "student_info": student_info,
        "completed_courses": completed_courses,
        "in_progress_courses": in_progress_courses,
        "required_courses": required_courses,
        "requirements_summary": _generate_requirements_summary(student_info, required_courses),
    }


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
    Extract completed courses.
    pdfplumber puts a space between the course number and the title:
      APPH 1040 Sci Foundation of Health A 2 Fall 2023
      HIST 2112 United States since 1877 A 3 Spring 2024
      BIOS 1108L Organismal Biology T 1 Fall 2024
    """
    seen: set = set()
    completed = []

    # [^\S\n]+ = horizontal whitespace only — prevents crossing newline boundaries
    pattern = re.compile(
        r'\b([A-Z]{2,5})[^\S\n]+(\d{4}[A-Z]?)[^\S\n]+([^\n]+?)[^\S\n]+([A-F][+-]?|T)[^\S\n]+(\d{1,2})[^\S\n]+(Fall|Spring|Summer)[^\S\n]+(\d{4})\b'
    )

    for match in pattern.finditer(text):
        dept, number, title, grade, credits_str, semester, year = match.groups()
        course_code = f"{dept} {number}"

        # Skip in-progress (captured by the other function) and withdrawn
        if grade in ('W',):
            continue
        if course_code in seen:
            continue
        seen.add(course_code)

        completed.append({
            "course_code": course_code,
            "course_name": title.strip(),
            "grade": grade,
            "credits": int(credits_str),
            "term": f"{semester} {year}",
        })

    return completed


def _extract_in_progress_courses(text: str) -> List[Dict]:
    """
    Extract in-progress courses.
    Format: DEPT NUM Title IP (credits) Term Year
    Example: MATH 1554 Linear Algebra IP (4) Spring 2026
    """
    seen: set = set()
    in_progress = []

    pattern = re.compile(
        r'\b([A-Z]{2,5})[^\S\n]+(\d{4}[A-Z]?)[^\S\n]+([^\n]+?)[^\S\n]+IP[^\S\n]+\((\d{1,2})\)[^\S\n]+(Fall|Spring|Summer)[^\S\n]+(\d{4})\b'
    )

    for match in pattern.finditer(text):
        dept, number, title, credits_str, semester, year = match.groups()
        course_code = f"{dept} {number}"

        if course_code in seen:
            continue
        seen.add(course_code)

        in_progress.append({
            "course_code": course_code,
            "course_name": title.strip(),
            "credits": int(credits_str),
            "term": f"{semester} {year}",
        })

    return in_progress


def _extract_required_courses(text: str) -> List[Dict]:
    """
    Extract required courses that still need to be completed
    Parse "Still needed" lines
    Format: "Still needed:1 Class in CS 2340" (no line breaks)
    """
    required = []

    # Handles simple and multiple-choice requirements, including cross-dept:
    #   "Still needed: 1 Class in CS 1100"
    #   "Still needed: 1 Class in CS 2050 or 2051"
    #   "Still needed: 1 Class in MATH 3215 or 3670 or CEE 3770 or ISYE 3770"
    pattern = re.compile(
        r'Still\s+needed:\s*(\d+)\s+Class(?:es)?\s+in\s+([A-Z]{2,5})\s+(\d{4})'
        r'((?:\s+or\s+(?:[A-Z]{2,5}\s+)?\d{4})*)',
        re.IGNORECASE
    )

    for match in re.finditer(pattern, text):
        num_classes = int(match.group(1))
        first_dept = match.group(2)
        first_num = match.group(3)
        rest = match.group(4)  # " or 2051 or CEE 3770 ..."

        course_codes = [f"{first_dept} {first_num}"]

        # Parse remaining "or [DEPT] NNNN" options
        for opt in re.finditer(r'or\s+(?:([A-Z]{2,5})\s+)?(\d{4})', rest, re.IGNORECASE):
            dept = opt.group(1) if opt.group(1) else first_dept
            course_codes.append(f"{dept} {opt.group(2)}")

        required.append({
            "courses": course_codes,
            "credits": num_classes * 3,
            "is_choice": len(course_codes) > 1,
            "is_elective": False,
        })

    return required


def _generate_requirements_summary(student_info: Dict, required_courses: List[Dict]) -> Dict:
    """Generate a summary of requirements"""
    credits_needed = max(0, student_info["credits_required"] - student_info["credits_applied"])

    return {
        "total_credits_needed": credits_needed,
        "core_requirements_met": credits_needed < 40,
        "major_requirements_remaining": len(required_courses),
        "estimated_semesters_remaining": max(1, credits_needed // 15)
    }


# Test function
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m utils.gatech_parser <path_to_degreeworks.pdf>")
        sys.exit(1)

    test_pdf_path = sys.argv[1]
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

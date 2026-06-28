"""
Georgia Tech DegreeWorks Parser

Parses Georgia Tech DegreeWorks PDF academic evaluations.
Uses pdfplumber as primary extractor (handles DegreeWorks PDFs reliably),
falls back to PyPDF2 if pdfplumber is not available.
"""

import re
from typing import Dict, List
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


def _extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text from PDF using pdfplumber (preferred) or PyPDF2 fallback."""
    # Try pdfplumber first — handles complex multi-column layouts much better
    try:
        import pdfplumber
        with pdfplumber.open(BytesIO(pdf_content)) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text(layout=False)
                if text:
                    pages.append(text)
            full_text = "\n".join(pages)
            if full_text.strip():
                return full_text
    except Exception as e:
        logger.warning(f"pdfplumber extraction failed, trying PyPDF2: {e}")

    # Fallback to PyPDF2
    try:
        import PyPDF2
        pdf_file = BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        pages = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        pdf_file.close()
        return "\n".join(pages)
    except Exception as e:
        logger.warning(f"PyPDF2 extraction failed: {e}")

    # Last resort: pypdf (modern fork of PyPDF2)
    try:
        from pypdf import PdfReader
        pdf_file = BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)
    except Exception as e:
        raise RuntimeError(f"Could not extract text from PDF. Tried pdfplumber, PyPDF2, and pypdf. Last error: {e}")


def parse_gatech_degreeworks(pdf_content: bytes) -> Dict:
    """
    Parse Georgia Tech DegreeWorks PDF.

    Returns dict with student_info, completed_courses, in_progress_courses,
    required_courses, and requirements_summary.
    """
    try:
        full_text = _extract_text_from_pdf(pdf_content)
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        raise ValueError(f"Could not read PDF file. Make sure it is a valid DegreeWorks PDF. ({e})")

    if not full_text or len(full_text.strip()) < 50:
        raise ValueError(
            "PDF appears to be empty or scanned (no extractable text). "
            "Export from DegreeWorks as a digital PDF, not a scan."
        )

    # Verify this looks like a Georgia Tech DegreeWorks document
    if "Georgia Tech" not in full_text and "BSCS" not in full_text and "DegreeWorks" not in full_text:
        raise ValueError("This does not appear to be a Georgia Tech DegreeWorks PDF.")

    student_info = _extract_student_info(full_text)
    completed_courses = _extract_completed_courses(full_text)
    in_progress_courses = _extract_in_progress_courses(full_text)
    required_courses = _extract_required_courses(full_text)

    return {
        "student_info": student_info,
        "completed_courses": completed_courses,
        "in_progress_courses": in_progress_courses,
        "required_courses": required_courses,
        "requirements_summary": _generate_requirements_summary(student_info, required_courses),
    }


def _extract_student_info(text: str) -> Dict:
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
        "college": "",
    }

    # Student name: "Student name  Student, Sample"
    name_match = re.search(
        r'Student\s+name\s+([A-Za-z][A-Za-z\-]+,\s+[A-Za-z][A-Za-z\-]+(?:\s+[A-Z])?)', text
    )
    if name_match:
        info["student_name"] = name_match.group(1).strip()

    # Fallback: header "Georgia Tech  Student, Sample  000000000"
    if not info["student_name"]:
        name_match = re.search(r'Georgia\s+Tech\s+([A-Za-z][A-Za-z\-]+,\s+[A-Za-z][A-Za-z\-]+)', text)
        if name_match:
            info["student_name"] = name_match.group(1).strip()

    # Student ID
    id_match = re.search(r'Student\s+ID\s+(\d{7,10})', text)
    if id_match:
        info["student_id"] = id_match.group(1).strip()

    # Degree
    degree_match = re.search(r'Degree\s+(BS\s+in\s+[A-Za-z\s]+?)(?:Audit|Program|Major|\n)', text)
    if degree_match:
        info["degree"] = degree_match.group(1).strip()

    # Major
    major_match = re.search(r'Major\s+([A-Za-z][A-Za-z\s]+?)(?:Program|Concentration|College|\n)', text)
    if major_match:
        info["major"] = major_match.group(1).strip()

    # Concentration (e.g. "BSCS: Media-People" or "BSCS: MediaPeople")
    conc_match = re.search(r'Concentration\s+(BSCS[:\s][^\n]+?)(?:College|Program|Major|\n)', text)
    if conc_match:
        info["concentration"] = conc_match.group(1).strip()

    # College
    college_match = re.search(r'College\s+(College of [A-Za-z\s]+?)(?:BSCS|Program|Major|\n)', text)
    if college_match:
        info["college"] = college_match.group(1).strip()

    # Overall GPA (first match = degree-level GPA)
    gpa_match = re.search(r'GPA:\s*([\d.]+)', text)
    if gpa_match:
        try:
            info["gpa"] = float(gpa_match.group(1))
        except ValueError:
            pass

    # Credits: "Credits required: 126 Credits applied: 89"
    credits_match = re.search(r'Credits\s+required:\s*(\d+)\s*Credits\s+applied:\s*(\d+)', text)
    if credits_match:
        try:
            info["credits_required"] = int(credits_match.group(1))
            info["credits_applied"] = int(credits_match.group(2))
        except ValueError:
            pass

    return info


def _extract_completed_courses(text: str) -> List[Dict]:
    """
    Extract completed courses (grade A/B/C/D/F, T for transfer, V for validation).
    """
    completed = []
    seen = set()

    pattern = re.compile(
        r'\b([A-Z]{2,5})\s+(\d{4}[A-Z]?)\s+'
        r'(.+?)\s+'
        r'([A-F][+-]?|T|V)\s+'
        r'(\d+)\s+'
        r'(Fall|Spring|Summer)\s+(\d{4})',
        re.MULTILINE
    )

    for m in pattern.finditer(text):
        dept = m.group(1)
        num = m.group(2)
        title = m.group(3).strip()
        grade = m.group(4)
        credits = int(m.group(5))
        sem = m.group(6)
        year = m.group(7)

        course_code = f"{dept} {num}"
        key = (course_code, grade, sem, year)
        if key in seen:
            continue
        seen.add(key)

        if re.match(r'^Satisfied\s+by', title, re.IGNORECASE):
            continue

        completed.append({
            "course_code": course_code,
            "course_name": title,
            "grade": grade,
            "credits": credits,
            "term": f"{sem} {year}",
        })

    return completed


def _extract_in_progress_courses(text: str) -> List[Dict]:
    """Extract in-progress courses (marked IP)."""
    in_progress = []
    seen = set()

    pattern = re.compile(
        r'\b([A-Z]{2,5})\s+(\d{4}[A-Z]?)\s+'
        r'(.+?)\s+'
        r'IP\s+\((\d+)\)\s+'
        r'(Fall|Spring|Summer)\s+(\d{4})',
        re.MULTILINE
    )

    for m in pattern.finditer(text):
        dept = m.group(1)
        num = m.group(2)
        title = m.group(3).strip()
        credits = int(m.group(4))
        sem = m.group(5)
        year = m.group(6)

        course_code = f"{dept} {num}"
        if course_code in seen:
            continue
        seen.add(course_code)

        in_progress.append({
            "course_code": course_code,
            "course_name": title,
            "credits": credits,
            "term": f"{sem} {year}",
        })

    return in_progress


def _extract_required_courses(text: str) -> List[Dict]:
    """
    Extract courses still needed. Handles:
      Still needed: 1 Class in CS 1100
      Still needed: 1 Class in CS 2050 or 2051
      Still needed: 3 Classes in CS 3451 or 4455 or 4460 ...
      Still needed: 1 Class in MATH 3215 or 3670 or CEE 3770 or ISYE 3770
    """
    required = []

    base_pattern = re.compile(
        r'Still\s+needed:\s*(\d+)\s+Class(?:es)?\s+in\s+([A-Z]{2,5})\s+(\d{4})'
        r'((?:\s+or\s+(?:[A-Z]{2,5}\s+)?\d{4})*)',
        re.IGNORECASE
    )

    for m in base_pattern.finditer(text):
        num_needed = int(m.group(1))
        first_dept = m.group(2)
        first_num = m.group(3)
        rest = m.group(4)

        course_codes = [f"{first_dept} {first_num}"]

        for opt in re.finditer(r'or\s+(?:([A-Z]{2,5})\s+)?(\d{4})', rest, re.IGNORECASE):
            dept = opt.group(1) if opt.group(1) else first_dept
            course_codes.append(f"{dept} {opt.group(2)}")

        required.append({
            "courses": course_codes,
            "credits": num_needed * 3,
            "is_choice": len(course_codes) > 1,
            "is_elective": False,
        })

    return required


def _generate_requirements_summary(student_info: Dict, required_courses: List[Dict]) -> Dict:
    credits_applied = student_info.get("credits_applied", 0)
    credits_required = student_info.get("credits_required", 126)
    credits_needed = max(0, credits_required - credits_applied)

    return {
        "total_credits_needed": credits_needed,
        "core_requirements_met": credits_needed < 40,
        "major_requirements_remaining": len(required_courses),
        "estimated_semesters_remaining": max(1, credits_needed // 15),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m utils.gatech_parser <path_to_degreeworks.pdf>")
        sys.exit(1)

    with open(sys.argv[1], "rb") as f:
        content = f.read()

    result = parse_gatech_degreeworks(content)

    print("\nStudent Info:")
    for k, v in result["student_info"].items():
        print(f"  {k}: {v}")

    print(f"\nCompleted ({len(result['completed_courses'])}):")
    for c in result["completed_courses"][:8]:
        print(f"  {c['course_code']} - {c['course_name']} ({c['grade']}, {c['credits']}cr, {c['term']})")

    print(f"\nIn-Progress ({len(result['in_progress_courses'])}):")
    for c in result["in_progress_courses"]:
        print(f"  {c['course_code']} - {c['course_name']} ({c['credits']}cr, {c['term']})")

    print(f"\nStill Needed ({len(result['required_courses'])}):")
    for r in result["required_courses"][:8]:
        print(f"  {r['courses']} ({r['credits']}cr)")

    print(f"\nSummary: {result['requirements_summary']}")

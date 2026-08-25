"""
Academic Evaluation Parser
Extracts course requirements and progress from GSU DegreeWorks PDFs.
Uses pdfplumber for reliable text extraction.
"""

import re
import json
import os
from typing import Dict, List, Optional
from utils.prerequisite_resolver import grade_value, is_passing_grade
from io import BytesIO

try:
    import pdfplumber
    _HAS_PDFPLUMBER = True
except ImportError:
    _HAS_PDFPLUMBER = False

try:
    import PyPDF2
    _HAS_PYPDF2 = True
except ImportError:
    _HAS_PYPDF2 = False


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def parse_academic_eval(file_content: bytes) -> Dict:
    text = _extract_text(file_content)
    return {
        "student_info": _parse_student_info(text),
        "completed_courses": _parse_completed_courses(text),
        "in_progress_courses": _parse_in_progress_courses(text),
        "required_courses": _parse_required_courses(text),
        "requirements_summary": _parse_requirements_summary(text),
        # raw_text intentionally excluded from return value for size
    }


def get_next_semester_recommendations(eval_data: Dict, school: str = "Georgia State University") -> Dict:
    """Return which required courses have all prerequisites met."""
    completed_codes = {c["course_code"] for c in eval_data.get("completed_courses", [])}
    in_progress_codes = {c["course_code"] for c in eval_data.get("in_progress_courses", [])}
    all_taken = completed_codes | in_progress_codes

    course_names = _load_course_names(school)

    # GSU prerequisite map (extend as needed)
    prerequisites: Dict[str, List[str]] = {
        "CSC 2720": ["CSC 1302"],
        "CSC 3210": ["CSC 2720"],
        "CSC 3320": ["CSC 2720"],
        "CSC 3350": ["CSC 2720"],
        "CSC 4320": ["CSC 3320"],
        "CSC 4330": ["CSC 3320"],
        "CSC 4351": ["CSC 3350"],
        "CSC 4352": ["CSC 4351"],
        "CSC 4520": ["CSC 2720", "MATH 2420"],
        "MATH 2212": ["MATH 2211"],
        "MATH 2641": ["MATH 2211"],
        "MATH 3020": ["MATH 2211"],
        # Georgia Tech
        "CS 1332": ["CS 1331"],
        "CS 2340": ["CS 1332"],
        "CS 3510": ["CS 1332", "MATH 2550"],
        "CS 3600": ["CS 1332"],
        "CS 4400": ["CS 1332"],
        "CS 4510": ["CS 3510"],
        "MATH 1554": ["MATH 1552"],
        "MATH 2550": ["MATH 1552"],
    }

    available, needs_prereqs = [], []

    for req in eval_data.get("required_courses", []):
        for course_code in req.get("courses", []):
            code = course_code.strip().upper()
            if code in all_taken or "@" in code:
                continue

            prereqs = prerequisites.get(code, [])
            prereqs_met = all(p in all_taken for p in prereqs)
            info = {
                "course_code": code,
                "course_name": course_names.get(code, ""),
                "credits": req.get("credits", 3),
                "prerequisites": prereqs,
                "prerequisites_met": prereqs_met,
            }

            if prereqs_met:
                available.append(info)
            else:
                info["missing_prerequisites"] = [p for p in prereqs if p not in all_taken]
                needs_prereqs.append(info)

    if "tech" not in school.lower():
        _fill_missing_names_from_banner(available + needs_prereqs)

    return {
        "available_courses": available,
        "prerequisites_met": [c["course_code"] for c in available],
        "prerequisites_needed": needs_prereqs,
    }


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

def _extract_text(pdf_content: bytes) -> str:
    """
    Extract text using pdfplumber (preferred) or PyPDF2 as fallback.
    pdfplumber preserves whitespace/columns far better than PyPDF2 on DegreeWorks PDFs.
    """
    if _HAS_PDFPLUMBER:
        try:
            with pdfplumber.open(BytesIO(pdf_content)) as pdf:
                pages = []
                for page in pdf.pages:
                    text = page.extract_text(x_tolerance=3, y_tolerance=3)
                    if text:
                        pages.append(text)
            return "\n".join(pages)
        except Exception as e:
            print(f"pdfplumber failed, falling back to PyPDF2: {e}")

    if _HAS_PYPDF2:
        try:
            reader = PyPDF2.PdfReader(BytesIO(pdf_content))
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
        except Exception as e:
            print(f"PyPDF2 also failed: {e}")

    raise RuntimeError("No PDF extraction library available. Install pdfplumber.")


# ---------------------------------------------------------------------------
# Student info
# ---------------------------------------------------------------------------

def _parse_student_info(text: str) -> Dict:
    info = {
        "student_name": "",
        "student_id": "",
        "gpa": None,
        "major": "",
        "college": "",
        "degree": "",
        "credits_required": 120,
        "credits_applied": 0,
        "catalog_year": "",
        "academic_standing": "",
        "advisor": "",
    }

    # Name  — "Student name  LastName, FirstName" or "Student name: LastName, FirstName"
    m = re.search(r"Student\s+name[:\s]+([A-Za-z]+,\s*[A-Za-z\s\-']+)", text, re.IGNORECASE)
    if m:
        info["student_name"] = m.group(1).strip()

    # Student ID (may be masked with asterisks)
    m = re.search(r"Student\s+ID[:\s]+[\*]*(\d{4,10})", text, re.IGNORECASE)
    if m:
        info["student_id"] = m.group(1)

    # GPA — "GSU GPA  3.45" or "Cumulative GPA: 3.45"
    for pattern in [
        r"GSU\s+GPA[:\s]+(\d+\.\d+)",
        r"Cumulative\s+GPA[:\s]+(\d+\.\d+)",
        r"Overall\s+GPA[:\s]+(\d+\.\d+)",
        r"GPA[:\s]+(\d+\.\d+)",
    ]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            info["gpa"] = float(m.group(1))
            break

    # Credits required / applied
    m = re.search(r"Credits\s+required[:\s]+(\d+)\s+Credits\s+applied[:\s]+(\d+)", text, re.IGNORECASE)
    if m:
        info["credits_required"] = int(m.group(1))
        info["credits_applied"] = int(m.group(2))
    else:
        # Fallback: individual lookups
        m = re.search(r"Credits\s+required[:\s]+(\d+)", text, re.IGNORECASE)
        if m:
            info["credits_required"] = int(m.group(1))
        m = re.search(r"Credits\s+applied[:\s]+(\d+)", text, re.IGNORECASE)
        if m:
            info["credits_applied"] = int(m.group(1))

    # Major — several DegreeWorks header formats
    major_patterns = [
        r"Majors?/Pathway\s+(?:(?:HS|BS|BA|MS|MA|AS|BBA):\s*)?(.+?)\s+College",
        r"Major[:\s]+([A-Za-z0-9\-\s&,\[\]]+?)(?:\s+(?:College|Degree|Credits|Catalog)|$)",
        r"(?:BS|BA|MS|MA|AS|BBA)\s+(?:Degree\s+-\s+)?([A-Za-z0-9\-\s&,\[\]]+?)(?:\s+(?:INCOMPLETE|COMPLETE|College)|$)",
        r"Program[:\s]+([A-Za-z0-9\-\s&,\[\]]+?)(?:\s+(?:College|Degree)|$)",
    ]
    for pattern in major_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            major = m.group(1).strip()
            # Strip degree-type prefixes that leaked through
            for prefix in ("HS:", "BS:", "BA:", "MS:", "MA:", "AS:", "BBA:", "in "):
                if major.upper().startswith(prefix.upper()):
                    major = major[len(prefix):].strip()
            # Remove bracketed codes like [CSCI]
            major = re.sub(r"\s*\[[\w\s]+\]\s*", " ", major).strip()
            major = re.sub(r"\s+(INCOMPLETE|COMPLETE|IN-PROGRESS).*$", "", major, flags=re.IGNORECASE).strip()
            if len(major) > 3:
                info["major"] = major
                break

    # College
    m = re.search(r"College\s+([A-Za-z0-9\s&,\.]+?)(?=Degree|$)", text)
    if m:
        info["college"] = m.group(1).strip()

    # Catalog year
    m = re.search(r"Catalog\s+year[:\s]+(\d{4}[-–]\d{2,4})", text, re.IGNORECASE)
    if m:
        info["catalog_year"] = m.group(1)

    # Academic standing
    m = re.search(r"Academic\s+Standing[:\s]+([A-Za-z\s]+?)(?=Department|Advisor|$)", text, re.IGNORECASE)
    if m:
        info["academic_standing"] = m.group(1).strip()

    # Advisor
    m = re.search(r"Advisor[:\s]+([A-Za-z]+,\s*[A-Za-z\s]+)", text, re.IGNORECASE)
    if m:
        info["advisor"] = m.group(1).strip()

    return info


# ---------------------------------------------------------------------------
# Completed courses
# ---------------------------------------------------------------------------

# DegreeWorks course line format (extracted from PDF):
#   CSC 1301 PRINCIPLES OF COMPUTER SCI I B 4 Fall Semester 2023
#   or (credits run together with term):
#   CSC 1301 PRINCIPLES OF COMPUTER SCI I B 4Fall Semester 2023
#
# Grade codes: A+/A/A-/B+/B/B-/C+/C/C-/D+/D/D-/F  W=withdraw  T=transfer  IP=in-progress  NA=in-progress
# We keep everything except W (withdrawn) and NA/IP (in-progress, handled separately).

_COURSE_RE = re.compile(
    r"([A-Z]{2,5})\s+(\d{4}[A-Z]?)\s+"           # dept + number (e.g. CSC 1301, BIOL 2107L)
    r"([A-Z][A-Z\s&\-:/]+?)\s+"                   # course name (greedy-but-minimal)
    r"([A-DF][+\-]?|[TWI]|IP|TR|NA)\s*"           # grade
    r"\(?(\d+)\)?\s*"                              # credits (optionally parenthesized)
    r"((?:Fall|Spring|Summer)\s+(?:Semester\s+)?\d{4})",  # term
    re.IGNORECASE,
)

_SKIP_GRADES = {"NA", "IP", "W", "-W"}


def _parse_completed_courses(text: str) -> List[Dict]:
    seen: Dict[str, Dict] = {}

    for m in _COURSE_RE.finditer(text):
        dept, number, name, grade, credits, term = (
            m.group(1).upper(), m.group(2), m.group(3).strip(),
            m.group(4).upper(), int(m.group(5)), m.group(6).strip(),
        )

        if grade in _SKIP_GRADES:
            continue

        code = f"{dept} {number}"
        course = {
            "course_code": code,
            "course_name": name,
            "grade": grade,
            "credits": credits,
            "term": term,
        }

        if code not in seen:
            seen[code] = course
        else:
            # Keep the better grade (e.g. retake)
            if grade_value(grade) > grade_value(seen[code]["grade"]):
                seen[code] = course

    # Drop attempts that earned no credit. A DegreeWorks audit lists failed courses
    # in its "Insufficient, Withdrawn, Repeated" block, and counting them as
    # completed both inflates the course history and lets a failed course satisfy a
    # prerequisite. Dedup runs first, so a course later passed keeps the passing
    # attempt; only courses whose *best* attempt was an F are dropped.
    return [c for c in seen.values() if is_passing_grade(c["grade"])]


# ---------------------------------------------------------------------------
# In-progress courses
# ---------------------------------------------------------------------------

_IN_PROGRESS_RE = re.compile(
    r"([A-Z]{2,5})\s+(\d{4}[A-Z]?)\s+"
    r"([A-Z][A-Z\s&\-:/]+?)\s+"
    r"(?:NA|IP)\s*"
    r"\(?(\d+)\)?\s*"
    r"((?:Fall|Spring|Summer)\s+(?:Semester\s+)?\d{4})",
    re.IGNORECASE,
)


def _parse_in_progress_courses(text: str) -> List[Dict]:
    # Try to narrow to the In-progress section first; fall back to full text
    section_match = re.search(r"In.progress(.+?)(?:Not Counted|Legend|Still needed|$)", text, re.DOTALL | re.IGNORECASE)
    search_text = section_match.group(1) if section_match else text

    seen = {}
    for m in _IN_PROGRESS_RE.finditer(search_text):
        dept, number, name, credits, term = (
            m.group(1).upper(), m.group(2), m.group(3).strip(),
            int(m.group(4)), m.group(5).strip(),
        )
        code = f"{dept} {number}"
        if code not in seen:
            seen[code] = {"course_code": code, "course_name": name, "credits": credits, "term": term}

    return list(seen.values())


# ---------------------------------------------------------------------------
# Required (still-needed) courses
# ---------------------------------------------------------------------------

# "Still needed: 4 Credits in CSC 3350"
# "Still needed: 3 Credits in CSC 4320 or 4330"
_STILL_NEEDED_RE = re.compile(
    r"Still\s+needed[:\s]+(\d+)\s+Credits?\s+in\s+([A-Z@\d\s]+?)(?:\s+Except\s+([A-Z\d\s,]+?))?(?=Still\s+needed|$|\n)",
    re.IGNORECASE,
)


def _parse_required_courses(text: str) -> List[Dict]:
    required = []

    for m in _STILL_NEEDED_RE.finditer(text):
        credits = int(m.group(1))
        course_spec = m.group(2).strip()
        exceptions = m.group(3).strip() if m.group(3) else ""

        # Elective wildcard (e.g. "CSC 3@ or 4@")
        if "@" in course_spec:
            required.append({
                "credits": credits,
                "courses": [course_spec],
                "exceptions": exceptions,
                "is_choice": True,
                "is_elective": True,
                "requirement_type": "elective",
            })
            continue

        # May contain "or" alternatives: "CSC 4320 or 4330" or "CSC 4320 or CSC 4330"
        if re.search(r"\bor\b", course_spec, re.IGNORECASE):
            parts = re.split(r"\s+or\s+", course_spec, flags=re.IGNORECASE)
            # Resolve bare numbers to the base department of the first entry
            base_dept_m = re.match(r"([A-Z]{2,5})", parts[0])
            base_dept = base_dept_m.group(1) if base_dept_m else ""
            options = []
            for part in parts:
                part = part.strip()
                if re.match(r"[A-Z]{2,5}\s+\d", part):
                    options.append(part)
                elif re.match(r"\d{4}", part) and base_dept:
                    options.append(f"{base_dept} {part}")
            required.append({
                "credits": credits,
                "courses": options or [course_spec],
                "is_choice": True,
                "requirement_type": "major",
            })
        else:
            required.append({
                "credits": credits,
                "courses": [course_spec],
                "is_choice": False,
                "requirement_type": "major",
            })

    return required


# ---------------------------------------------------------------------------
# Requirements summary
# ---------------------------------------------------------------------------

def _parse_requirements_summary(text: str) -> Dict:
    summary = {
        "degree_name": "",
        "total_credits_required": 120,
        "total_credits_completed": 0,
        "sections": [],
    }

    m = re.search(r"(BS|BA|MS|MA|AS|BBA)\s+(?:Degree\s+-\s+)?([A-Za-z\s\-]+?)(?:\s+(?:INCOMPLETE|COMPLETE))", text, re.IGNORECASE)
    if m:
        summary["degree_name"] = f"{m.group(1).upper()} {m.group(2).strip()}"

    for sect_m in re.finditer(r"([\w\s\-]{5,60}?)\s+(COMPLETE|INCOMPLETE|IN-PROGRESS|SEE ADVISOR)", text, re.IGNORECASE):
        name = sect_m.group(1).strip()
        if name and name != "Georgia State University":
            summary["sections"].append({"name": name, "status": sect_m.group(2).upper()})

    return summary


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_course_names(school: str) -> Dict[str, str]:
    names: Dict[str, str] = {}
    catalog_dir = os.path.join(os.path.dirname(__file__), "..", "data", "course_catalogs")

    try:
        for filename in os.listdir(catalog_dir):
            if not filename.endswith(".json"):
                continue
            try:
                with open(os.path.join(catalog_dir, filename), "r") as f:
                    catalog = json.load(f)
                for code, info in catalog.get("courses", {}).items():
                    if isinstance(info, dict):
                        names[code] = info.get("name", "")
                for section in catalog.get("degree_requirements", {}).values():
                    if isinstance(section, list):
                        for c in section:
                            if c.get("course_code") and c.get("course_name"):
                                names[c["course_code"]] = c["course_name"]
            except Exception:
                continue
    except Exception:
        pass

    try:
        from utils.prerequisites import COURSE_DATABASE
        for code, info in COURSE_DATABASE.items():
            if code not in names:
                names[code] = info.get("name", "")
    except ImportError:
        pass

    return names


def _fill_missing_names_from_banner(courses: List[Dict]) -> None:
    missing = [c for c in courses if not c.get("course_name")]
    if not missing:
        return

    subjects = {c["course_code"].split()[0] for c in missing if " " in c["course_code"]}
    if not subjects:
        return

    try:
        from utils.gsu_banner_api import GSUBannerAPI
        api = GSUBannerAPI()
        term = api.get_current_term()
        banner_names: Dict[str, str] = {}

        for subject in subjects:
            try:
                for section in (api.search_courses(term, subject, page_max_size=100) or []):
                    code = f"{section.get('subject', '')} {section.get('courseNumber', '')}"
                    title = section.get("courseTitle", "")
                    if code and title and code not in banner_names:
                        banner_names[code] = title
            except Exception:
                continue

        for c in missing:
            if banner_names.get(c["course_code"]):
                c["course_name"] = banner_names[c["course_code"]]
    except Exception:
        pass


# ---------------------------------------------------------------------------
# CLI convenience
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python academic_eval_parser.py <path/to/transcript.pdf>")
        sys.exit(1)

    with open(sys.argv[1], "rb") as f:
        result = parse_academic_eval(f.read())

    info = result["student_info"]
    print(f"Student : {info['student_name']} ({info['student_id']})")
    print(f"Major   : {info['major']}")
    print(f"GPA     : {info['gpa']}")
    print(f"Credits : {info['credits_applied']} / {info['credits_required']}")
    print(f"\nCompleted ({len(result['completed_courses'])} courses):")
    for c in result["completed_courses"][:10]:
        print(f"  {c['course_code']:12} {c['grade']:4} {c['course_name']}")
    print(f"\nIn-progress ({len(result['in_progress_courses'])} courses):")
    for c in result["in_progress_courses"]:
        print(f"  {c['course_code']:12} {c['course_name']}")
    print(f"\nStill needed ({len(result['required_courses'])} requirements):")
    for r in result["required_courses"][:10]:
        print(f"  {r['credits']} cr: {r['courses']}")

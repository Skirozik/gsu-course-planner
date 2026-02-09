"""
Academic Evaluation Parser
Extracts course requirements and progress from GSU academic evaluation PDFs
"""

import PyPDF2
import re
import json
import os
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

    # Major/Pathway - try multiple patterns to handle different DegreeWorks formats
    major_patterns = [
        # Pattern 1: Majors/Pathway BS: Major Name College (with optional [CODE])
        r'Majors?/Pathway\s+(?:(?:HS|BS|BA|MS|MA):\s*)?([A-Za-z0-9\-\s&,\[\]]+?)\s+College',
        # Pattern 2: Major: Major Name
        r'Major:\s+([A-Za-z0-9\-\s&,\[\]]+?)(?:\s+(?:College|Degree|Credits)|$)',
        # Pattern 3: BS in Major Name or BS Major Name
        r'(?:BS|BA|MS|MA)\s+(?:in\s+)?([A-Za-z0-9\-\s&,\[\]]+?)(?:\s+(?:INCOMPLETE|COMPLETE|College)|$)',
        # Pattern 4: Majors/Pathway without College
        r'Majors?/Pathway\s+(?:(?:HS|BS|BA|MS|MA):\s*)?([A-Za-z0-9\-\s&,\[\]]+?)(?:\s+(?:Degree|Credits|Catalog)|$)',
        # Pattern 5: Program or Plan
        r'(?:Program|Plan):\s+([A-Za-z0-9\-\s&,\[\]]+?)(?:\s+(?:College|Degree|Credits)|$)',
    ]

    major_found = False
    for pattern in major_patterns:
        major_match = re.search(pattern, text, re.IGNORECASE)
        if major_match:
            major_text = major_match.group(1).strip()
            # Remove common prefixes if they weren't caught by the regex
            for prefix in ['HS:', 'BS:', 'BA:', 'MS:', 'MA:', 'in']:
                if major_text.upper().startswith(prefix.upper()):
                    major_text = major_text[len(prefix):].strip()
            # Clean up any trailing noise
            major_text = re.sub(r'\s+(INCOMPLETE|COMPLETE|IN-PROGRESS).*$', '', major_text, flags=re.IGNORECASE)
            # Remove bracketed codes like [CSCI] or [CS]
            major_text = re.sub(r'\s*\[[\w\s]+\]\s*', ' ', major_text).strip()
            if major_text and len(major_text) > 3:  # Sanity check
                info["major"] = major_text
                major_found = True
                break

    # If no major found, try to extract from degree name
    if not major_found:
        degree_match = re.search(r'(?:BS|BA|MS|MA|AS)\s+(?:Degree\s+-\s+)?([A-Za-z0-9\-\s&,\[\]]+?)(?:\s+(?:INCOMPLETE|COMPLETE)|$)', text, re.IGNORECASE)
        if degree_match:
            major_text = degree_match.group(1).strip()
            # Remove bracketed codes like [CSCI]
            major_text = re.sub(r'\s*\[[\w\s]+\]\s*', ' ', major_text).strip()
            info["major"] = major_text

    # College - handle both "College of ..." and other college name formats
    college_match = re.search(r'College\s+([A-Za-z0-9\s&,\.]+?)(?=Degree|$)', text)
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
    # Note: In actual GSU PDFs, there's often NO SPACE between credits and term (e.g., "3Fall")
    course_pattern = re.compile(
        r'([A-Z]{2,4})\s+(\d{4}[A-Z]?)\s+'  # Course code (e.g., CSC 1301, BIOL 1103L)
        r'([A-Z][A-Z\s&\-:]+?)\s+'           # Course name
        r'([A-DF][+-]?|T|W|NA)\s+'           # Grade (added T for transfer credits)
        r'\(?(\d+)\)?\s*'                     # Credits (may be in parentheses, OPTIONAL space after)
        r'((?:Fall|Spring|Summer)\s+Semester\s+\d{4})',  # Term
        re.IGNORECASE
    )

    for match in course_pattern.finditer(text):
        dept = match.group(1).upper()
        number = match.group(2)
        name = match.group(3).strip()
        grade = match.group(4).upper()
        credits = int(match.group(5))
        term = match.group(6).replace('\n', ' ').strip()  # Clean up newlines in term

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


def _load_course_names(school: str) -> Dict[str, str]:
    """Load course code -> course name mapping from all available sources"""
    names = {}
    catalog_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'course_catalogs')

    # Load ALL catalog files to cover multiple departments
    try:
        for filename in os.listdir(catalog_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(catalog_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        catalog = json.load(f)

                    # Pull names from the "courses" section
                    courses = catalog.get("courses", {})
                    for code, info in courses.items():
                        if isinstance(info, dict):
                            names[code] = info.get("name", "")

                    # Also pull from degree_requirements sections
                    deg_reqs = catalog.get("degree_requirements", {})
                    for section in deg_reqs:
                        items = deg_reqs[section]
                        if isinstance(items, list):
                            for course in items:
                                code = course.get("course_code", "")
                                name = course.get("course_name", "")
                                if code and name:
                                    names[code] = name
                except Exception:
                    continue
    except Exception:
        pass

    # Fallback: try the prerequisites database
    try:
        from utils.prerequisites import COURSE_DATABASE
        for code, info in COURSE_DATABASE.items():
            if code not in names:
                names[code] = info.get("name", "")
    except ImportError:
        pass

    # Common GSU cross-department courses that CS students often need
    common_courses = {
        # CIS courses
        "CIS 2010": "Computer Information Systems",
        "CIS 3100": "Management Information Systems",
        "CIS 3260": "Business Application Programming",
        "CIS 3300": "Systems Analysis",
        "CIS 3310": "Database Management",
        "CIS 4120": "Networking Concepts",
        "CIS 4130": "Information Security",
        # English
        "ENGL 1101": "English Composition I",
        "ENGL 1102": "English Composition II",
        "ENGL 1103": "Advanced English Composition",
        # History
        "HIST 2110": "Survey of United States History to 1877",
        "HIST 2111": "Survey of United States History Since 1877",
        # Political Science
        "POLS 1101": "American Government",
        # Economics
        "ECON 2105": "Principles of Macroeconomics",
        "ECON 2106": "Principles of Microeconomics",
        # Philosophy
        "PHIL 1010": "Critical Thinking",
        "PHIL 2020": "Ethics and Society",
        # Science
        "PHYS 1111": "Introductory Physics I",
        "PHYS 1111L": "Introductory Physics I Lab",
        "PHYS 1112": "Introductory Physics II",
        "PHYS 1112L": "Introductory Physics II Lab",
        "PHYS 2211": "Principles of Physics I",
        "PHYS 2211L": "Principles of Physics I Lab",
        "PHYS 2212": "Principles of Physics II",
        "PHYS 2212L": "Principles of Physics II Lab",
        "CHEM 1211": "Principles of Chemistry I",
        "CHEM 1211L": "Principles of Chemistry I Lab",
        "CHEM 1212": "Principles of Chemistry II",
        "CHEM 1212L": "Principles of Chemistry II Lab",
        # Communication
        "COMM 1100": "Human Communication",
        # Psychology
        "PSYC 1101": "Introduction to Psychology",
        # Sociology
        "SOCI 1101": "Introduction to Sociology",
        # Art
        "ART 1010": "Drawing I",
        "MUSC 1100": "Music Appreciation",
    }
    for code, name in common_courses.items():
        if code not in names:
            names[code] = name

    return names


def get_next_semester_recommendations(eval_data: Dict, school: str = "Georgia State University") -> Dict:
    """
    Analyze the evaluation data and recommend courses for next semester

    Args:
        eval_data: Parsed academic evaluation data
        school: School name (for course code formatting)

    Returns:
        Dictionary with recommended courses and reasoning
    """
    completed_codes = [c["course_code"] for c in eval_data["completed_courses"]]
    in_progress_codes = [c["course_code"] for c in eval_data["in_progress_courses"]]
    all_taken = completed_codes + in_progress_codes

    # Load course name mappings from catalog
    course_names = _load_course_names(school)

    recommendations = {
        "available_courses": [],
        "prerequisites_met": [],
        "prerequisites_needed": []
    }

    # Define prerequisite chains for CS courses (school-specific)
    if "tech" in school.lower():
        # Georgia Tech course codes (CS XXXX)
        prerequisites = {
            "CS 1332": ["CS 1331"],  # Data Structures requires OOP
            "CS 2340": ["CS 1332"],  # Objects & Design requires Data Structures
            "CS 3510": ["CS 1332", "MATH 2550"],  # Design & Analysis requires DS and Discrete Math
            "CS 3600": ["CS 1332"],  # Intro to AI requires Data Structures
            "CS 4400": ["CS 1332"],  # Database Systems requires Data Structures
            "CS 4510": ["CS 3510"],  # Automata requires Design & Analysis
            "MATH 1554": ["MATH 1552"],  # Linear Algebra requires Integral Calculus
            "MATH 2550": ["MATH 1552"],  # Discrete Math requires Integral Calculus
        }
    else:
        # Georgia State University course codes (CSC XXXX)
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
                "course_name": course_names.get(course_code, ""),
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

    # Banner API fallback: look up names for any courses still missing them
    if "tech" not in school.lower():
        _fill_missing_names_from_banner(recommendations["available_courses"] + recommendations["prerequisites_needed"])

    return recommendations


def _fill_missing_names_from_banner(courses: List[Dict]) -> None:
    """Look up missing course names from the GSU Banner API (in-place)"""
    # Find courses with no name
    missing = [c for c in courses if not c.get("course_name")]
    if not missing:
        return

    # Group by subject to minimize API calls (one call per subject)
    subjects_needed = set()
    for c in missing:
        parts = c["course_code"].split()
        if len(parts) >= 1:
            subjects_needed.add(parts[0])

    if not subjects_needed:
        return

    try:
        from utils.gsu_banner_api import GSUBannerAPI
        api = GSUBannerAPI()
        term = api.get_current_term()

        # Build a lookup of course_code -> course_title from Banner
        banner_names = {}
        for subject in subjects_needed:
            try:
                raw_sections = api.search_courses(term, subject, page_max_size=100)
                for section in (raw_sections or []):
                    code = f"{section.get('subject', '')} {section.get('courseNumber', '')}"
                    title = section.get("courseTitle", "")
                    if code and title and code not in banner_names:
                        banner_names[code] = title
            except Exception:
                continue

        # Fill in missing names
        for c in missing:
            name = banner_names.get(c["course_code"], "")
            if name:
                c["course_name"] = name
    except Exception:
        pass  # If Banner API fails, just leave names empty


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

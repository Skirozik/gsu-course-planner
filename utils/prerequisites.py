"""
GSU Course Prerequisites Database
Contains prerequisite information for Computer Science and related courses
"""

from typing import Dict, List, Optional
from utils.prerequisite_resolver import meets_minimum_grade

# Comprehensive prerequisite database for CS and related courses
# Format: course_code -> {name, credits, prerequisites, corequisites, description}
COURSE_DATABASE: Dict[str, Dict] = {
    # Computer Science Core Courses
    "CSC 1301": {
        "name": "Principles of Computer Science I",
        "credits": 4,
        "prerequisites": [],
        "corequisites": ["MATH 1111"],
        "description": "Introduction to programming using Python. Covers variables, control structures, functions, and basic data structures.",
        "min_grade": "C"
    },
    "CSC 1302": {
        "name": "Principles of Computer Science II",
        "credits": 4,
        "prerequisites": ["CSC 1301"],
        "corequisites": [],
        "description": "Object-oriented programming in Java. Covers classes, inheritance, polymorphism, and basic algorithms.",
        "min_grade": "C"
    },
    "CSC 2720": {
        "name": "Data Structures",
        "credits": 3,
        "prerequisites": ["CSC 1302"],
        "corequisites": [],
        "description": "Fundamental data structures including arrays, linked lists, stacks, queues, trees, and graphs. Algorithm analysis.",
        "min_grade": "C"
    },
    "CSC 3210": {
        "name": "Computer Organization and Programming",
        "credits": 4,
        "prerequisites": ["CSC 2720"],
        "corequisites": [],
        "description": "Computer architecture, assembly language programming, memory organization, and I/O systems.",
        "min_grade": "C"
    },
    "CSC 3320": {
        "name": "System Level Programming",
        "credits": 3,
        "prerequisites": ["CSC 2720"],
        "corequisites": [],
        "description": "C programming, Unix/Linux systems, process management, memory management, and system calls.",
        "min_grade": "C"
    },
    "CSC 3350": {
        "name": "Software Development (CTW)",
        "credits": 4,
        "prerequisites": ["CSC 2720"],
        "corequisites": [],
        "description": "Software engineering principles, agile development, version control, testing, and team projects.",
        "min_grade": "C"
    },
    "CSC 4320": {
        "name": "Operating Systems",
        "credits": 4,
        "prerequisites": ["CSC 3320"],
        "corequisites": [],
        "description": "Process scheduling, memory management, file systems, concurrency, and distributed systems.",
        "min_grade": "C"
    },
    "CSC 4330": {
        "name": "Programming Language Concepts",
        "credits": 4,
        "prerequisites": ["CSC 3320"],
        "corequisites": [],
        "description": "Syntax, semantics, type systems, functional programming, and language implementation.",
        "min_grade": "C"
    },
    "CSC 4351": {
        "name": "Capstone Senior Design I",
        "credits": 2,
        "prerequisites": ["CSC 3350"],
        "corequisites": [],
        "description": "First semester of senior capstone project. Project planning, requirements, and initial design.",
        "min_grade": "C"
    },
    "CSC 4352": {
        "name": "Capstone Senior Design II",
        "credits": 2,
        "prerequisites": ["CSC 4351"],
        "corequisites": [],
        "description": "Second semester of senior capstone. Implementation, testing, and final presentation.",
        "min_grade": "C"
    },
    "CSC 4520": {
        "name": "Design and Analysis of Algorithms",
        "credits": 4,
        "prerequisites": ["CSC 2720", "MATH 2420"],
        "corequisites": [],
        "description": "Algorithm design techniques, complexity analysis, NP-completeness, and advanced data structures.",
        "min_grade": "C"
    },

    # Computer Science Electives
    "CSC 4210": {
        "name": "Computer Networks",
        "credits": 4,
        "prerequisites": ["CSC 3320"],
        "corequisites": [],
        "description": "Network protocols, TCP/IP, routing, network security, and distributed applications.",
        "min_grade": "C"
    },
    "CSC 4350": {
        "name": "Software Engineering",
        "credits": 4,
        "prerequisites": ["CSC 3350"],
        "corequisites": [],
        "description": "Advanced software engineering topics, design patterns, and software architecture.",
        "min_grade": "C"
    },
    "CSC 4360": {
        "name": "Mobile Application Development",
        "credits": 4,
        "prerequisites": ["CSC 3350"],
        "corequisites": [],
        "description": "Development of mobile applications for iOS and Android platforms.",
        "min_grade": "C"
    },
    "CSC 4370": {
        "name": "Web Development",
        "credits": 4,
        "prerequisites": ["CSC 2720"],
        "corequisites": [],
        "description": "Full-stack web development including HTML, CSS, JavaScript, and backend frameworks.",
        "min_grade": "C"
    },
    "CSC 4510": {
        "name": "Automata",
        "credits": 4,
        "prerequisites": ["CSC 2720", "MATH 2420"],
        "corequisites": [],
        "description": "Finite automata, regular expressions, context-free grammars, and Turing machines.",
        "min_grade": "C"
    },
    "CSC 4610": {
        "name": "Artificial Intelligence",
        "credits": 4,
        "prerequisites": ["CSC 2720"],
        "corequisites": [],
        "description": "Search algorithms, knowledge representation, machine learning fundamentals, and AI applications.",
        "min_grade": "C"
    },
    "CSC 4620": {
        "name": "Machine Learning",
        "credits": 4,
        "prerequisites": ["CSC 2720", "MATH 3020"],
        "corequisites": [],
        "description": "Supervised and unsupervised learning, neural networks, and practical ML applications.",
        "min_grade": "C"
    },
    "CSC 4710": {
        "name": "Database Systems",
        "credits": 4,
        "prerequisites": ["CSC 2720"],
        "corequisites": [],
        "description": "Relational databases, SQL, database design, normalization, and transaction processing.",
        "min_grade": "C"
    },
    "CSC 4740": {
        "name": "Data Mining",
        "credits": 4,
        "prerequisites": ["CSC 2720"],
        "corequisites": [],
        "description": "Data preprocessing, classification, clustering, association rules, and big data analytics.",
        "min_grade": "C"
    },
    "CSC 4810": {
        "name": "Computer Graphics",
        "credits": 4,
        "prerequisites": ["CSC 2720", "MATH 2641"],
        "corequisites": [],
        "description": "2D/3D graphics, transformations, rendering, and graphics programming with OpenGL.",
        "min_grade": "C"
    },
    "CSC 4820": {
        "name": "Game Programming",
        "credits": 4,
        "prerequisites": ["CSC 2720"],
        "corequisites": [],
        "description": "Game design principles, game engines, physics simulation, and game AI.",
        "min_grade": "C"
    },
    "CSC 4850": {
        "name": "Cybersecurity",
        "credits": 4,
        "prerequisites": ["CSC 3320"],
        "corequisites": [],
        "description": "Network security, cryptography, secure coding, and security protocols.",
        "min_grade": "C"
    },

    # Mathematics Courses
    "MATH 1001": {
        "name": "Quantitative Reasoning",
        "credits": 3,
        "prerequisites": [],
        "corequisites": [],
        "description": "Mathematical reasoning and problem-solving skills.",
        "min_grade": "C"
    },
    "MATH 1111": {
        "name": "College Algebra",
        "credits": 3,
        "prerequisites": [],
        "corequisites": [],
        "description": "Functions, equations, inequalities, and polynomial operations.",
        "min_grade": "C"
    },
    "MATH 1113": {
        "name": "Precalculus",
        "credits": 3,
        "prerequisites": ["MATH 1111"],
        "corequisites": [],
        "description": "Trigonometry, exponential and logarithmic functions, preparation for calculus.",
        "min_grade": "C"
    },
    "MATH 2211": {
        "name": "Calculus of One Variable I",
        "credits": 4,
        "prerequisites": ["MATH 1113"],
        "corequisites": [],
        "description": "Limits, derivatives, integrals, and applications of calculus.",
        "min_grade": "C"
    },
    "MATH 2212": {
        "name": "Calculus of One Variable II",
        "credits": 4,
        "prerequisites": ["MATH 2211"],
        "corequisites": [],
        "description": "Integration techniques, sequences, series, and parametric equations.",
        "min_grade": "C"
    },
    "MATH 2420": {
        "name": "Discrete Mathematics",
        "credits": 3,
        "prerequisites": ["MATH 1113"],
        "corequisites": [],
        "description": "Logic, sets, relations, functions, combinatorics, and graph theory.",
        "min_grade": "C"
    },
    "MATH 2641": {
        "name": "Linear Algebra",
        "credits": 3,
        "prerequisites": ["MATH 2211"],
        "corequisites": [],
        "description": "Vectors, matrices, linear transformations, eigenvalues, and applications.",
        "min_grade": "C"
    },
    "MATH 3020": {
        "name": "Applied Probability and Statistics",
        "credits": 3,
        "prerequisites": ["MATH 2211"],
        "corequisites": [],
        "description": "Probability theory, random variables, distributions, and statistical inference.",
        "min_grade": "C"
    },

    # Science Courses
    "BIOL 1103": {
        "name": "Introductory Biology I",
        "credits": 3,
        "prerequisites": [],
        "corequisites": ["BIOL 1103L"],
        "description": "Cell biology, genetics, and evolution.",
        "min_grade": "D"
    },
    "BIOL 1103L": {
        "name": "Introductory Biology I Lab",
        "credits": 1,
        "prerequisites": [],
        "corequisites": ["BIOL 1103"],
        "description": "Laboratory component for BIOL 1103.",
        "min_grade": "D"
    },
    "BIOL 1104": {
        "name": "Introductory Biology II",
        "credits": 3,
        "prerequisites": ["BIOL 1103"],
        "corequisites": ["BIOL 1104L"],
        "description": "Ecology, plant biology, and animal biology.",
        "min_grade": "D"
    },
    "BIOL 1104L": {
        "name": "Introductory Biology II Lab",
        "credits": 1,
        "prerequisites": ["BIOL 1103L"],
        "corequisites": ["BIOL 1104"],
        "description": "Laboratory component for BIOL 1104.",
        "min_grade": "D"
    },
    "PHYS 2211": {
        "name": "Principles of Physics I",
        "credits": 4,
        "prerequisites": ["MATH 2211"],
        "corequisites": ["PHYS 2211L"],
        "description": "Mechanics, waves, and thermodynamics.",
        "min_grade": "D"
    },
    "PHYS 2211L": {
        "name": "Principles of Physics I Lab",
        "credits": 1,
        "prerequisites": [],
        "corequisites": ["PHYS 2211"],
        "description": "Laboratory component for PHYS 2211.",
        "min_grade": "D"
    },
    "ASTR 1010K": {
        "name": "Astronomy of the Solar System",
        "credits": 4,
        "prerequisites": [],
        "corequisites": [],
        "description": "Introduction to the solar system, planets, and space exploration.",
        "min_grade": "D"
    },
    "GEOL 1121": {
        "name": "Introductory Geology I",
        "credits": 3,
        "prerequisites": [],
        "corequisites": ["GEOL 1121L"],
        "description": "Earth materials, processes, and geological time.",
        "min_grade": "D"
    },
    "GEOL 1121L": {
        "name": "Introductory Geology I Lab",
        "credits": 1,
        "prerequisites": [],
        "corequisites": ["GEOL 1121"],
        "description": "Laboratory component for GEOL 1121.",
        "min_grade": "D"
    },
}


def get_course_info(course_code: str) -> Optional[Dict]:
    """Get full information about a course"""
    course_code = course_code.upper().strip()
    return COURSE_DATABASE.get(course_code)


def get_prerequisites(course_code: str) -> List[str]:
    """Get list of prerequisite courses for a given course"""
    course_code = course_code.upper().strip()
    course = COURSE_DATABASE.get(course_code)
    if course:
        return course.get("prerequisites", [])
    return []


def get_corequisites(course_code: str) -> List[str]:
    """Get list of corequisite courses for a given course"""
    course_code = course_code.upper().strip()
    course = COURSE_DATABASE.get(course_code)
    if course:
        return course.get("corequisites", [])
    return []


def get_all_prerequisites(course_code: str, visited: set = None) -> List[str]:
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

    direct_prereqs = get_prerequisites(course_code)
    for prereq in direct_prereqs:
        # Get prerequisites of prerequisites first
        deeper_prereqs = get_all_prerequisites(prereq, visited)
        for p in deeper_prereqs:
            if p not in all_prereqs:
                all_prereqs.append(p)
        # Then add this prerequisite
        if prereq not in all_prereqs:
            all_prereqs.append(prereq)

    return all_prereqs


def check_prerequisites_met(
    course_code: str,
    completed_courses: List[str],
    grades: Optional[Dict[str, str]] = None,
) -> Dict:
    """
    Check if prerequisites are met for a given course

    Args:
        course_code: the course to test eligibility for
        completed_courses: course codes the student has taken or is taking
        grades: optional {course_code: letter grade}. When supplied, a prerequisite
            counts only if the grade clears this course's ``min_grade`` — a D earns
            credit toward the degree but does not unlock a course requiring a C.
            Codes absent from the mapping (an in-progress enrolment, say) are
            treated as satisfying, because there is no grade to judge yet.

    Returns:
        Dict with:
        - can_take: bool
        - met: list of met prerequisites
        - missing: list of missing prerequisites
        - below_grade: prerequisites taken but not at the required grade
    """
    course_code = course_code.upper().strip()
    completed_upper = {c.upper().strip() for c in completed_courses}

    prereqs = get_prerequisites(course_code)
    min_grade = COURSE_DATABASE.get(course_code, {}).get("min_grade")
    grade_map = {k.upper().strip(): v for k, v in (grades or {}).items()}

    met, missing, below_grade = [], [], []
    for p in prereqs:
        if p not in completed_upper:
            missing.append(p)
        elif grades is not None and p in grade_map and not meets_minimum_grade(grade_map[p], min_grade):
            below_grade.append(p)
            missing.append(p)
        else:
            met.append(p)

    return {
        "can_take": len(missing) == 0,
        "met": met,
        "missing": missing,
        "below_grade": below_grade,
        "all_prerequisites": prereqs
    }


def get_courses_unlocked_by(course_code: str) -> List[str]:
    """Get list of courses that have this course as a prerequisite"""
    course_code = course_code.upper().strip()
    unlocked = []

    for code, info in COURSE_DATABASE.items():
        if course_code in info.get("prerequisites", []):
            unlocked.append(code)

    return unlocked


def search_courses(query: str) -> List[Dict]:
    """Search courses by code or name"""
    query = query.upper().strip()
    results = []

    for code, info in COURSE_DATABASE.items():
        if query in code or query in info["name"].upper():
            results.append({
                "course_code": code,
                **info
            })

    return results


def get_prerequisite_tree(course_code: str) -> Dict:
    """
    Build a tree structure showing all prerequisites

    Returns nested dict showing prerequisite hierarchy
    """
    course_code = course_code.upper().strip()
    course = COURSE_DATABASE.get(course_code)

    if not course:
        return {"course_code": course_code, "error": "Course not found"}

    tree = {
        "course_code": course_code,
        "name": course["name"],
        "credits": course["credits"],
        "prerequisites": []
    }

    for prereq in course.get("prerequisites", []):
        prereq_tree = get_prerequisite_tree(prereq)
        tree["prerequisites"].append(prereq_tree)

    return tree


def format_prerequisite_chain(course_code: str) -> str:
    """Format the prerequisite chain as a readable string"""
    course_code = course_code.upper().strip()
    course = COURSE_DATABASE.get(course_code)

    if not course:
        return f"Course {course_code} not found in database."

    lines = []
    lines.append(f"📚 {course_code}: {course['name']} ({course['credits']} credits)")
    lines.append(f"   {course['description']}")

    prereqs = course.get("prerequisites", [])
    coreqs = course.get("corequisites", [])

    if prereqs:
        lines.append(f"\n📋 Prerequisites (must complete first):")
        for prereq in prereqs:
            prereq_info = COURSE_DATABASE.get(prereq, {})
            prereq_name = prereq_info.get("name", "Unknown")
            lines.append(f"   • {prereq}: {prereq_name}")

            # Show prerequisites of prerequisites
            deeper = get_prerequisites(prereq)
            if deeper:
                lines.append(f"     └─ Requires: {', '.join(deeper)}")
    else:
        lines.append(f"\n✅ No prerequisites required!")

    if coreqs:
        lines.append(f"\n🔗 Corequisites (take at same time):")
        for coreq in coreqs:
            coreq_info = COURSE_DATABASE.get(coreq, {})
            coreq_name = coreq_info.get("name", "Unknown")
            lines.append(f"   • {coreq}: {coreq_name}")

    # Show full chain
    full_chain = get_all_prerequisites(course_code)
    if full_chain:
        lines.append(f"\n📍 Full prerequisite chain (in order):")
        lines.append(f"   {' → '.join(full_chain)} → {course_code}")

    # Show what this course unlocks
    unlocks = get_courses_unlocked_by(course_code)
    if unlocks:
        lines.append(f"\n🔓 Completing this course unlocks:")
        for unlock in unlocks[:5]:  # Limit to 5
            unlock_info = COURSE_DATABASE.get(unlock, {})
            lines.append(f"   • {unlock}: {unlock_info.get('name', 'Unknown')}")
        if len(unlocks) > 5:
            lines.append(f"   ... and {len(unlocks) - 5} more")

    return "\n".join(lines)


def get_all_cs_courses() -> List[Dict]:
    """Get all Computer Science courses"""
    cs_courses = []
    for code, info in COURSE_DATABASE.items():
        if code.startswith("CSC"):
            cs_courses.append({
                "course_code": code,
                **info
            })
    return sorted(cs_courses, key=lambda x: x["course_code"])


def get_all_math_courses() -> List[Dict]:
    """Get all Mathematics courses"""
    math_courses = []
    for code, info in COURSE_DATABASE.items():
        if code.startswith("MATH"):
            math_courses.append({
                "course_code": code,
                **info
            })
    return sorted(math_courses, key=lambda x: x["course_code"])


# Example usage
if __name__ == "__main__":
    # Test the functions
    print(format_prerequisite_chain("CSC 4520"))
    print("\n" + "="*50 + "\n")
    print(format_prerequisite_chain("CSC 4320"))

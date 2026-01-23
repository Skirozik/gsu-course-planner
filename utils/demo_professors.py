"""
Demo Professor Data

Maps courses to sample professors for testing RMP integration.
In production, this would come from GSU's course schedule system.
"""

# Sample professor assignments for demo purposes
# Format: course_code -> professor_name
DEMO_PROFESSORS = {
    # Computer Science
    "CSC 1301": "Robert Robinson",
    "CSC 1302": "Sarah Chen",
    "CSC 2510": "Michael Johnson",
    "CSC 2720": "David Kim",
    "CSC 3210": "Jennifer Lee",
    "CSC 3220": "Thomas Anderson",
    "CSC 3320": "Emily Rodriguez",
    "CSC 4210": "James Wilson",
    "CSC 4220": "Maria Garcia",
    "CSC 4320": "Christopher Brown",
    "CSC 4330": "Patricia Martinez",
    "CSC 4520": "Daniel Taylor",
    "CSC 4710": "Lisa Thompson",
    "CSC 4720": "Kevin White",
    "CSC 4810": "Susan Harris",

    # Math
    "MATH 1111": "Robert Davis",
    "MATH 1113": "Nancy Clark",
    "MATH 2211": "John Lewis",
    "MATH 2212": "Karen Walker",
    "MATH 2420": "Steven Hall",
    "MATH 3030": "Amy Allen",
    "MATH 3200": "Brian Young",

    # CIS (Business School)
    "CIS 2200": "Michelle Scott",
    "CIS 3260": "Andrew King",
    "CIS 3300": "Rebecca Wright",
    "CIS 3400": "Joshua Green",
    "CIS 3500": "Amanda Baker",
    "CIS 4200": "Matthew Adams",
    "CIS 4400": "Lauren Nelson",
    "CIS 4500": "Ryan Carter",
    "CIS 4970": "Nicole Mitchell",
    "CIS 4980": "Brandon Perez",

    # Business Core
    "ACCT 2101": "Victoria Roberts",
    "ACCT 2102": "William Turner",
    "ECON 2105": "Stephanie Phillips",
    "ECON 2106": "Gregory Campbell",
    "BUSA 2100": "Rachel Parker",
    "BUSA 3000": "Timothy Evans",
    "FI 3300": "Christina Edwards",
    "MGT 3400": "Jonathan Collins",
    "MK 3400": "Samantha Stewart",
    "BUSA 4850": "Nicholas Morris",

    # Health Sciences
    "HS 3120": "Elizabeth Rogers",
    "HS 3300": "Charles Reed",
    "HS 3400": "Margaret Cook",
    "HS 4100": "Paul Morgan",
    "HS 4500": "Barbara Bell",
    "HSC 2110": "Richard Murphy",
    "HSC 3100": "Linda Bailey",
    "BIOL 2107": "George Rivera",
    "BIOL 2108": "Helen Cooper",

    # Georgia Tech courses
    "CS 1301": "David Joyner",
    "CS 1331": "Monica Sweat",
    "CS 1332": "Mary Hudachek-Buswell",
    "CS 2050": "Lance Fortnow",
    "CS 2110": "Bill Leahy",
    "CS 2340": "Mark Moss",
    "CS 3510": "Eric Vigoda",
    "CS 3600": "Thad Starner",
    "CS 4400": "Leo Mark",
    "CS 4641": "Charles Isbell",
}


def add_demo_professors(courses: list, use_demo_mode: bool = True) -> list:
    """
    Add sample professor names to courses for demo purposes

    Args:
        courses: List of course dicts (must have 'course_code')
        use_demo_mode: If True, adds demo professors. If False, returns as-is

    Returns:
        Same courses with 'professor' field added
    """
    if not use_demo_mode:
        return courses

    for course in courses:
        course_code = course.get('course_code', '')

        # Add professor from demo data
        if course_code in DEMO_PROFESSORS:
            course['professor'] = DEMO_PROFESSORS[course_code]
        else:
            # Default for courses not in our demo list
            course['professor'] = 'Staff'

    return courses


def get_professor_for_course(course_code: str) -> str:
    """
    Get demo professor name for a course

    Args:
        course_code: Course code (e.g., "CSC 3320")

    Returns:
        Professor name or "Staff" if not found
    """
    return DEMO_PROFESSORS.get(course_code, "Staff")


def is_real_professor(professor_name: str) -> bool:
    """
    Check if this is a real professor name (not TBA/Staff)

    Args:
        professor_name: Professor name to check

    Returns:
        True if real professor, False if placeholder
    """
    if not professor_name:
        return False

    placeholder_names = ['tba', 'staff', 'tbd', 'pending', 'n/a']
    return professor_name.lower() not in placeholder_names


# Note for production deployment:
"""
🚀 PRODUCTION DEPLOYMENT NOTE:

For a production app, you would:

1. Scrape Professor Data from GSU Course Schedule:
   - PAWS registration system
   - Course schedule pages
   - Banner API if available

2. Store in Database:
   CREATE TABLE course_sections (
       semester VARCHAR(20),
       course_code VARCHAR(20),
       section VARCHAR(10),
       professor VARCHAR(100),
       schedule VARCHAR(200)
   );

3. Update Each Semester:
   - Parse course schedule when published
   - Update professor assignments
   - Track historical data

4. Handle Multiple Sections:
   - Same course, different professors
   - Let students choose section
   - Show all options with RMP ratings

This demo data is just to show how the RMP integration works!
"""

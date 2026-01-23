# Prerequisite Resolution System

## Overview

The prerequisite resolution layer parses raw prerequisite text from course catalogs and evaluates student eligibility based on completed courses and grades.

## Key Features

✅ **Grade-Aware Evaluation**: Checks if students meet minimum grade requirements (e.g., "C or higher")
✅ **Complex Logic Parsing**: Handles AND/OR logic in prerequisites
✅ **Multiple Formats**: Parses various prerequisite text patterns
✅ **Detailed Reasoning**: Provides human-readable explanations for eligibility
✅ **In-Progress Course Handling**: Excludes courses currently being taken

## Architecture

### Components

1. **`PrerequisiteResolver`** (`utils/prerequisite_resolver.py`)
   - Core parsing and evaluation engine
   - Parses raw prerequisite text into structured format
   - Evaluates eligibility against student transcripts

2. **`CatalogLoader` Enhancement** (`utils/catalog_loader.py`)
   - New methods: `check_prerequisites_with_grades()` and `get_eligible_courses_with_grades()`
   - Integrates resolver with existing catalog system
   - Provides high-level API for eligibility checking

3. **Catalog Data** (`data/course_catalogs/cs_major.json`)
   - Contains `prerequisites_raw` field with exact catalog text
   - 52 CSC courses with prerequisite data scraped from GSU catalog

## Usage Examples

### Basic Eligibility Check

```python
from utils.catalog_loader import get_catalog_loader

catalog = get_catalog_loader()

# Student transcript with grades
completed_courses = [
    {"course_code": "CSC 3320", "grade": "B"}
]

# Check if student can take CSC 4320 (Operating Systems)
result = catalog.check_prerequisites_with_grades(
    school="Georgia State University",
    major="Computer Science",
    course_code="CSC 4320",
    completed_courses=completed_courses
)

print(f"Eligible: {result['eligible']}")  # True
print(f"Reason: {result['reason']}")      # "All prerequisites met"
```

### Get All Eligible Courses

```python
# Student transcript
completed = [
    {"course_code": "CSC 1301", "grade": "B"},
    {"course_code": "CSC 1302", "grade": "A"},
    {"course_code": "CSC 2720", "grade": "B"},
    {"course_code": "MATH 2420", "grade": "A"}
]

# Currently enrolled courses
in_progress = ["CSC 3210"]

# Get all courses the student can take
eligible_courses = catalog.get_eligible_courses_with_grades(
    school="Georgia State University",
    major="Computer Science",
    completed_courses=completed,
    in_progress_courses=in_progress,
    limit=10
)

for course in eligible_courses:
    print(f"{course['course_code']}: {course['course_name']}")
```

### Direct Resolver Usage

```python
from utils.prerequisite_resolver import check_course_eligibility

# Raw prerequisite text
prereq_text = "CSC 1301 with a C or higher"

# Student transcript
completed = [
    {"course_code": "CSC 1301", "grade": "D"}  # Too low!
]

result = check_course_eligibility(prereq_text, completed)

print(f"Eligible: {result['eligible']}")  # False
print(f"Reason: {result['reason']}")      # "Missing: CSC 1301 (min grade: C)"
```

## Supported Prerequisite Patterns

### Simple Prerequisite
```
"CSC 1301 with a C or higher"
```
Parsed as: CSC 1301 (min grade: C)

### OR Logic
```
"(CSC 2720 or DSCI 2720) with a C or higher"
```
Parsed as: CSC 2720 OR DSCI 2720 (min grade: C)

### Complex AND/OR
```
"(CSC 2720 or DSCI 2720) and either MATH 3020 or MATH 3030 with a C or higher"
```
Parsed as two groups (ANDed together):
- Group 1: CSC 2720 OR DSCI 2720 (min grade: C)
- Group 2: MATH 3020 OR MATH 3030 (min grade: C)

### Multiple AND Prerequisites
```
"CSC 2720, CSC 3210, and CSC 3320 with a C or higher"
```
Parsed as: CSC 2720 AND CSC 3210 AND CSC 3320 (min grade: C)

### Catalog Text Variations
The resolver automatically handles:
- "with a C or higher"
- "with grade of C or higher"
- "Students must meet..." (removed from parsing)
- "or permission of..." (removed from parsing)

## Grade Hierarchy

```python
GRADE_VALUES = {
    'A+': 13, 'A': 12, 'A-': 11,
    'B+': 10, 'B': 9, 'B-': 8,
    'C+': 7, 'C': 6, 'C-': 5,
    'D+': 4, 'D': 3, 'D-': 2,
    'F': 1
}
```

## Testing

### Run Unit Tests
```bash
python3 test_prerequisite_resolver.py
```

Tests all prerequisite parsing patterns and eligibility evaluation logic.

### Run Demo
```bash
python3 demo_prerequisite_resolution.py
```

Demonstrates the system using real GSU catalog data with sample student transcripts.

## Integration with Course Planner App

The prerequisite resolution system is automatically integrated into the Streamlit app. The catalog loader uses it when:

1. **Checking eligibility** for courses in catalog-based recommendations
2. **Filtering courses** that students are currently enrolled in
3. **Displaying course requirements** in the Catalog Explorer tab

### Future Enhancements

The app could use the enhanced prerequisite checking to:
- Show why a student can't take a course (missing specific prerequisites with grades)
- Highlight courses where student has the prerequisite but grade is too low
- Suggest retaking courses to meet grade requirements
- Build prerequisite chains showing path to advanced courses

## API Reference

### PrerequisiteResolver

#### `parse_prerequisites(prereq_text: str) -> List[PrerequisiteGroup]`
Parses raw prerequisite text into structured format.

#### `evaluate_eligibility(prereq_text: str, completed_courses: List[Dict], in_progress_courses: List[str]) -> Dict`
Evaluates if student meets prerequisites.

**Returns:**
```python
{
    "eligible": bool,
    "met_requirements": List[PrerequisiteRequirement],
    "missing_requirements": List[PrerequisiteRequirement],
    "reason": str,
    "prerequisite_groups": List[PrerequisiteGroup]
}
```

### CatalogLoader

#### `check_prerequisites_with_grades(school, major, course_code, completed_courses, in_progress_courses) -> Dict`
Enhanced prerequisite checking with grade evaluation.

#### `get_eligible_courses_with_grades(school, major, completed_courses, in_progress_courses, limit) -> List[Dict]`
Gets all courses student is eligible to take based on grades.

## Files

- **`utils/prerequisite_resolver.py`**: Core resolver implementation
- **`test_prerequisite_resolver.py`**: Unit tests
- **`demo_prerequisite_resolution.py`**: Demonstration script
- **`data/course_catalogs/cs_major.json`**: Catalog with prerequisite data
- **`data/parsed_prerequisites/csc_prerequisites_catalog_38.json`**: Raw scraped data

## Data Source

Prerequisite data is scraped from GSU's Modern Campus Catalog (catalog 38) and stored in `prerequisites_raw` fields. See `utils/gsu_prerequisite_parser.py` for the scraping implementation.

## Limitations

1. **Parsing Accuracy**: Complex prerequisite text with unusual phrasing may not parse perfectly
2. **Permission-based Prerequisites**: "or permission of instructor" requirements are not evaluated
3. **Test Scores**: Prerequisites like "SAT score of X" are not handled
4. **Course Equivalencies**: Alternative course codes must be explicitly listed in prerequisite text

## Contributing

To add support for new prerequisite patterns:

1. Add test case to `test_prerequisite_resolver.py`
2. Update parsing logic in `PrerequisiteResolver._parse_course_group()`
3. Run tests to ensure backward compatibility
4. Update this documentation

## License

Part of the GSU Course Planner project.

# Multi-Major Catalog System Guide

## Overview

Your course planner now supports **multiple majors** with dynamic prerequisite checking. Each major is defined in its own JSON catalog file.

## How It Works

### 1. **Catalog Structure**

Each major has its own JSON file in `data/course_catalogs/`:
- `cs_major.json` - Computer Science
- `business_major.json` - Business Administration
- *Add more majors as needed*

### 2. **JSON Format**

Each catalog contains:

```json
{
  "metadata": {
    "major": "Computer Science",
    "degree_type": "BS",
    "university": "Georgia State University",
    "catalog_year": "2025-2026",
    "total_credits_required": 120
  },
  "degree_requirements": {
    "core_courses": [...],      // Required courses
    "electives": [...],         // Elective options
    "math_requirements": [...]  // Math courses
  },
  "courses": {
    "CSC 1301": {
      "name": "Principles of Computer Science I",
      "credits": 4,
      "prerequisites": [],
      "corequisites": ["MATH 1111"],
      "description": "...",
      "min_grade": "C"
    },
    ...
  }
}
```

## Using the Catalog System

### Basic Usage

```python
from utils.catalog_loader import CatalogLoader

# Create loader instance
loader = CatalogLoader()

# Get available majors
majors = loader.get_available_majors()
# Output: ['Business Administration', 'Computer Science']

# Get core courses for a major
core = loader.get_core_courses("Computer Science")

# Get prerequisites for a course
prereqs = loader.get_prerequisites("Computer Science", "CSC 2720")
# Output: ['CSC 1302']

# Check if student can take a course
completed = ["CSC 1301", "CSC 1302"]
result = loader.check_prerequisites_met("Computer Science", "CSC 2720", completed)
# Output: {'can_take': True, 'met': ['CSC 1302'], 'missing': [], ...}

# Get recommended next courses
recommendations = loader.get_recommended_next_courses("Computer Science", completed, limit=5)

# Get degree progress
progress = loader.get_degree_progress("Computer Science", completed)
# Output: {'major': '...', 'core_progress': '2/11', 'completion_percentage': 15, ...}
```

### Key Methods

| Method | Purpose |
|--------|---------|
| `get_available_majors()` | List all supported majors |
| `get_catalog(major)` | Get full catalog for a major |
| `get_core_courses(major)` | Get required core courses |
| `get_elective_courses(major)` | Get available electives |
| `get_math_requirements(major)` | Get math course requirements |
| `get_course_info(major, course_code)` | Get details for a specific course |
| `get_prerequisites(major, course_code)` | Get direct prerequisites |
| `get_all_prerequisites(major, course_code)` | Get full prerequisite chain |
| `check_prerequisites_met(major, course, completed)` | Check if student can take a course |
| `get_courses_unlocked_by(major, course)` | See what courses a student unlocks |
| `get_recommended_next_courses(major, completed)` | Get courses the student can take next |
| `get_degree_progress(major, completed)` | Calculate degree completion % |

## Adding a New Major

1. **Create a JSON file** in `data/course_catalogs/` (e.g., `engineering_major.json`)

2. **Follow the template** from existing majors

3. **Include all courses** with:
   - Course code and name
   - Credits
   - Prerequisites (list of course codes)
   - Corequisites (courses taken simultaneously)
   - Description
   - Minimum grade required

4. **Restart the app** - the loader will auto-detect it

Example structure:
```json
{
  "metadata": {
    "major": "Engineering",
    "degree_type": "BS",
    ...
  },
  "degree_requirements": { ... },
  "courses": { ... }
}
```

## Integration with Your App

The system is ready to integrate into `app.py`:

```python
from utils.catalog_loader import get_catalog_loader

loader = get_catalog_loader()

# In your Streamlit app
major = st.selectbox("Select your major", loader.get_available_majors())

completed_courses = parse_academic_eval(uploaded_file)["completed_courses"]

# Show next courses
recommendations = loader.get_recommended_next_courses(major, completed_courses)

# Show progress
progress = loader.get_degree_progress(major, completed_courses)
st.progress(progress["completion_percentage"] / 100)
st.write(f"Core Progress: {progress['core_progress']}")
```

## Files Included

- **`data/course_catalogs/cs_major.json`** - Computer Science major
- **`data/course_catalogs/business_major.json`** - Business Administration major
- **`utils/catalog_loader.py`** - The catalog loading system

Ready to scale to any number of majors!

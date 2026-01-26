# Georgia Tech Bug Fixes - January 24, 2026

## Issues Reported
When uploading Georgia Tech DegreeWorks PDF, the app was showing:
1. ❌ Student name not showing
2. ❌ Major not showing
3. ❌ GPA not showing correctly
4. ❌ Completed courses not showing
5. ❌ Required courses not showing
6. ❌ "No available courses to enroll in next semester"
7. ❌ Personalized schedule section empty

## Root Causes Found

### Bug #1: School Selection Reset on File Upload ⚠️ CRITICAL
**Location**: `app.py` line 478
**Problem**: When uploading a new PDF file, the code reset `selected_school` to `None`, then immediately tried to check which school was selected to route to the correct parser. Since it was always `None`, it always used the GSU parser instead of the GT parser.

```python
# BEFORE (broken):
if file_hash != st.session_state.last_file_hash:
    st.session_state.selected_school = None  # ❌ Reset to None!

    # Then tries to use it:
    if st.session_state.selected_school == "Georgia Tech":  # Always False!
        parse_gatech_degreeworks(pdf_content)
    else:  # Always takes this path
        parse_academic_eval(pdf_content)  # Wrong parser for GT!
```

**Fix**: Don't reset `selected_school` when a new file is uploaded - it was already selected in Step 1.

```python
# AFTER (fixed):
if file_hash != st.session_state.last_file_hash:
    # DON'T reset selected_school - needed for parser routing!
    # selected_school determines which parser to use
```

**Impact**: This single bug caused all other issues - the GT PDF was being parsed with the GSU parser, which couldn't extract the data correctly.

---

### Bug #2: Hardcoded GSU Course Codes in Recommendations
**Location**: `utils/academic_eval_parser.py` line 386
**Problem**: The prerequisite checker only knew about GSU course codes (CSC 2720, CSC 3320, etc.) but Georgia Tech uses different codes (CS 1332, CS 2340, etc.).

```python
# BEFORE (broken):
prerequisites = {
    "CSC 2720": ["CSC 1302"],  # GSU codes only
    "CSC 3210": ["CSC 2720"],
    # ... no GT courses!
}
```

**Fix**: Made the function school-aware with separate prerequisite maps for each school.

```python
# AFTER (fixed):
def get_next_semester_recommendations(eval_data: Dict, school: str = "Georgia State University"):
    if "tech" in school.lower():
        # Georgia Tech course codes (CS XXXX)
        prerequisites = {
            "CS 1332": ["CS 1331"],
            "CS 2340": ["CS 1332"],
            # ... GT courses
        }
    else:
        # Georgia State University course codes (CSC XXXX)
        prerequisites = {
            "CSC 2720": ["CSC 1302"],
            # ... GSU courses
        }
```

**Impact**: GT students were getting "no available courses" because the system couldn't match their course codes.

---

### Bug #3: Required Courses Not Extracted from GT PDF
**Location**: `utils/gatech_parser.py` line 216
**Problem**: The required courses parser was only catching complex "Choose from following:" statements but missing simple "1 Class in CS 1100" entries.

**Test Result Before Fix**:
```
📝 Required Courses (2):
  ['Choose from 1 of the following:'] (3 credits)  ← Not helpful!
  ['Choose from 1 of the following:'] (3 credits)  ← Not helpful!
```

**Fix**: Added three new regex patterns to catch all types of requirements:
1. Simple: "Still needed:1 Class in CS 1100"
2. Choice: "Still needed:1 Class in CS 2050 or 2051"
3. Multi: "Still needed:3 Classes in CS 3451 or 4455 or 4460"

**Test Result After Fix**:
```
📝 Required Courses (12):
  CS 1100 (3 credits)
  CS 2050 (3 credits)
  MATH 2550 (3 credits)
  CS 2340 (3 credits)
  PSYC 2015 (3 credits)
  CS 3451 (9 credits)
  CS 3750 (3 credits)
  MATH 3012 (3 credits)
  CS 2050 OR CS 2051 (3 credits)
  CS 3451 OR CS 4455 OR CS 4460 OR CS 4464 OR CS 4475 OR CS 4480 (9 credits)
  CS 3750 OR CS 3751 (3 credits)
  CS 3451 OR CS 4455 OR CS 4460 OR CS 4464 OR CS 4475 OR CS 4480 (9 credits)
```

**Impact**: Now extracts 12 actual course requirements instead of 2 vague statements.

---

### Bug #4: Degree Field Capturing Too Much Text
**Location**: `utils/gatech_parser.py` line 97
**Problem**: Regex was too greedy and captured text after the degree name.

**Before**: `"BS in Computer ScienceAudit date"` ❌
**After**: `"BS in Computer Science"` ✅

**Fix**: Added lookahead to stop at keywords like "Audit", "Program", "Major".

---

### Bug #5: Concentration and College Fields Malformed
**Location**: `utils/gatech_parser.py` line 107-114
**Problem**: Regex patterns were capturing too much or too little text.

**Before**:
```
concentration: ""  ← Empty
college: "College of Computing    BSCS"  ← Extra junk
```

**After**:
```
concentration: "BSCS: Media-People"  ✅
college: "College of Computing"  ✅
```

**Fix**: Added better regex boundaries with lookahead patterns.

---

## Files Modified

1. **app.py**
   - Line 478: Don't reset `selected_school` on new file upload
   - Line 719: Pass school parameter to `get_next_semester_recommendations()`

2. **utils/academic_eval_parser.py**
   - Line 364: Made `get_next_semester_recommendations()` school-aware
   - Added Georgia Tech prerequisite map
   - Added Georgia State University prerequisite map

3. **utils/gatech_parser.py**
   - Line 97: Fixed degree field regex
   - Line 107: Fixed concentration field regex
   - Line 112: Fixed college field regex
   - Line 216: Completely rewrote required courses extraction with 3 new patterns

## Test Results After Fixes

### Student Info Extraction ✅
```
Student Name: Vo, Nhi N
Student ID: 903878789
Major: Computer Science
GPA: 3.55
Credits: 89/126 (70.6%)
Degree: BS in Computer Science
Concentration: BSCS: Media-People
College: College of Computing
```

### Completed Courses ✅
Successfully extracted 22 completed courses including:
- CS 1301, CS 1331, CS 2110, CS 3001
- MATH 1551, MATH 1552
- PHYS 2211, BIOS courses, etc.

### In-Progress Courses ✅
Successfully extracted 6 in-progress courses:
- MATH 1554, CS 1332, CS 3790, CS 4660, SCOE 2701, COE 2701

### Required Courses ✅
Successfully extracted 12 course requirements:
- Core: CS 1100, CS 2050, MATH 2550
- Major: CS 2340, CS 3451, CS 3750, MATH 3012
- Electives with choices (OR statements)

## What Should Work Now

1. ✅ **Student Info Display**: Name, major, GPA showing correctly
2. ✅ **Academic Summary**: All completed courses visible
3. ✅ **In-Progress Courses**: Current semester courses showing
4. ✅ **Required Courses**: Actual course codes instead of placeholders
5. ✅ **Course Recommendations**: Using GT course codes and prerequisites
6. ✅ **Banner API Integration**: GT sections pulling from correct API
7. ✅ **RateMyProfessors**: GT professors with correct school ID

## How to Test

1. Go to http://localhost:8501
2. Select **Georgia Tech** (not GSU!)
3. Upload Nhi's DegreeWorks PDF
4. Check that all student info appears in left column
5. Check that completed/in-progress courses show correctly
6. Submit preferences form
7. Verify course recommendations appear (should show CS 1100, CS 2050, MATH 2550, etc.)
8. Verify each course shows ranked sections from GT Banner API

## Known Limitations

1. **Prerequisites**: The hardcoded prerequisite map only covers core CS courses. More courses may need to be added.
2. **Complex Requirements**: "Choose from 1 of the following" style requirements are captured but not fully parsed into specific course lists.
3. **Transfer Credits**: Courses with grade "T" (transfer) are included but transfer institution not tracked.

## Next Steps for Full GT Support

1. **Expand Prerequisite Map**: Add more GT courses to the prerequisite checker
2. **Use Catalog Loader**: Switch from hardcoded prerequisites to the catalog JSON files
3. **Improve Complex Requirements**: Parse "Choose from following" sections to extract actual course lists
4. **Add More GT Courses**: Ensure all GT CS courses in `georgia_tech_cs_major.json` have correct prerequisites

---

**All critical bugs fixed! Georgia Tech integration should now work end-to-end.**

Last Updated: January 24, 2026

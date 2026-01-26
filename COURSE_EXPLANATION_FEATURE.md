# Course Explanation Feature - Implementation Summary

## Overview
Added AI-powered course explanations to help students understand why specific courses were recommended. This uses Option 1 (simple button approach) rather than a full chatbox for cost efficiency.

## What Was Implemented

### 1. New Function in `utils/llm_integration.py`

Added two new methods to the `CourseRecommender` class:

#### `generate_course_explanation()` (Line 171-223)
- Takes course code, course name, student data, preferences, available courses, and degree requirements
- Calls OpenAI API with optimized settings for cost:
  - Model: `gpt-4o-mini` (cheaper than gpt-4)
  - Max tokens: 300 (shorter for concise explanations)
  - Temperature: 0.5 (more focused responses)
  - Timeout: 15 seconds
- Returns formatted explanation string (2-3 bullet points)
- Graceful error handling with fallback message

#### `_build_explanation_prompt()` (Line 225-279)
- Constructs prompt with student context:
  - Completed courses (up to 10 most recent)
  - GPA and credits earned
  - Major
  - Career goals from preferences
- Course status:
  - Whether it's required or elective
  - Credit value
- Focuses AI on explaining:
  1. Prerequisites the student has met
  2. How course fits degree requirements
  3. What future courses/opportunities it unlocks

### 2. Integration in `app.py`

#### Session State Initialization (Line 393-397)
```python
if 'explanation_count' not in st.session_state:
    st.session_state.explanation_count = 0

if 'explanations_cache' not in st.session_state:
    st.session_state.explanations_cache = {}
```

#### Explanation UI (Line 956-1012)
Added expander under each recommended course with:
- **Cached explanations**: If student already requested explanation for a course, show cached version (no API call)
- **Usage limit**: Maximum 5 explanations per session to control API costs
- **Clear feedback**: Shows "Explanations used: X/5" counter
- **Button trigger**: "Generate AI Explanation" button to request explanation
- **Error handling**: Graceful fallback if API unavailable

## How It Works

### Student Experience

1. **View course recommendations** - Student sees their recommended courses
2. **Click "Why was this course recommended?"** - Expands explanation section
3. **Click "Generate AI Explanation"** button
4. **See AI-generated explanation** with 2-3 bullet points like:
   ```
   • You've successfully completed CS 1331 (Intro to OOP), meeting the
     prerequisite for this data structures course

   • CS 1332 is a required core course for your Computer Science degree,
     essential for progressing to upper-level CS courses

   • Completing this course will unlock CS 2340 (Objects & Design),
     CS 3510 (Design & Analysis), and other advanced CS courses
   ```

### Cost Control Features

1. **Limit to 5 explanations per session**
   - Prevents excessive API usage
   - Students can refresh page to reset if needed

2. **Caching per student + course**
   - Same student asking about same course = cached response (no API call)
   - Cache key: `{student_id}_{course_code}`

3. **Efficient API settings**
   - Uses `gpt-4o-mini` (10x cheaper than GPT-4)
   - Only 300 max tokens (short responses)
   - 15 second timeout

### Estimated Cost

- `gpt-4o-mini` pricing: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- Average explanation: ~500 input tokens + 150 output tokens = ~$0.0001 per explanation
- 5 explanations per student = ~$0.0005 per session
- **Very affordable!**

## Files Modified

1. **utils/llm_integration.py**
   - Added `generate_course_explanation()` method
   - Added `_build_explanation_prompt()` helper method

2. **app.py**
   - Added session state for explanation tracking (lines 393-397)
   - Added explanation UI under each course (lines 956-1012)

## Testing the Feature

1. **Start the app**
   ```bash
   streamlit run app.py
   ```

2. **Upload a DegreeWorks PDF** (Georgia State or Georgia Tech)

3. **Fill out preferences form**

4. **View recommended courses**

5. **Click "Why was this course recommended?"** under any course

6. **Click "Generate AI Explanation"** button

7. **Verify**:
   - Explanation appears as 2-3 bullet points
   - Counter shows "Explanations used: 1/5"
   - Clicking same course again shows cached explanation instantly
   - After 5 explanations, warning appears instead of button

## Example Explanation Output

For **CS 1332 - Data Structures & Algorithms**:

```
• You've completed CS 1331 (Object-Oriented Programming) with a B grade,
  satisfying the prerequisite for this course. Your strong foundation in
  OOP will help you understand how to implement complex data structures.

• CS 1332 is a required core course for your Computer Science major. It's
  essential for your degree progression and is needed before you can take
  most upper-level CS courses.

• Completing this course unlocks CS 2340 (Objects & Design), CS 3510
  (Design & Analysis of Algorithms), and CS 4400 (Database Systems) -
  all critical courses for your CS degree and career preparation.
```

## Benefits

1. **Student Understanding**: Students know exactly why each course was recommended
2. **Informed Decisions**: Helps students prioritize which courses to take
3. **Motivation**: Understanding the "why" increases student engagement
4. **Cost Effective**: Minimal API costs with caching and limits
5. **Simple UX**: Clean, non-intrusive button instead of complex chatbox

## Future Enhancements

Potential improvements if needed:
1. Increase limit from 5 to 10 explanations if cost allows
2. Add "Ask follow-up question" feature (would need more careful rate limiting)
3. Include professor recommendations in explanation
4. Add course difficulty insights based on RMP data
5. Persist cache across sessions using local storage

---

**Status**: ✅ Implemented and Ready for Testing

**Last Updated**: January 25, 2026

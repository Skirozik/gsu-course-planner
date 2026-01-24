# 🔄 Automated Professor & RMP Data Updates

## Overview

To move from **demo mode** to **production**, you need to automatically pull data from two sources:

1. **GSU Course Schedule** → Which professors teach which sections
2. **RateMyProfessors.com** → Ratings for those professors (we already do this!)

---

## Current State vs Production

### Current (Demo Mode):
```
generate_sample_sections() → Fake professors
      ↓
RMP API → Real ratings (but for fake professors)
      ↓
Rankings displayed
```

### Production (Automated):
```
GSU Schedule Scraper → Real professors + sections
      ↓
RMP API (cached) → Real ratings for real professors
      ↓
Rankings displayed
```

---

## Part 1: GSU Schedule Data (Missing Piece)

### What You Need

GSU's course schedule that shows:
- Course code (CSC 3320)
- Section number (001, 002, etc.)
- CRN (Course Registration Number)
- Instructor name
- Meeting times
- Location
- Seats available

### Where to Get It

**Option A: Scrape GSU Registration Site**
- URL: https://registration.gsu.edu
- Inspect HTML structure
- Use BeautifulSoup to parse

**Option B: PAWS/Banner API**
- Check if GSU provides an API
- Contact GSU IT department
- May require authorization

**Option C: Manual Data Entry** (temporary)
- Download course schedules as PDFs
- Parse PDFs to extract instructor data
- Update database manually each semester

### Implementation Steps

1. **Inspect GSU's site:**
```bash
# Visit GSU registration in your browser
open https://registration.gsu.edu

# Open DevTools (F12)
# Search for a course (e.g., CSC 3320)
# Inspect the HTML structure
# Note the CSS classes/IDs for:
#   - Section rows
#   - Instructor names
#   - CRN numbers
#   - Times/locations
```

2. **Update the scraper:**
```python
# Edit utils/gsu_schedule_scraper.py

# Update these in _parse_sections():
section_rows = soup.find_all('tr', class_='actual-class-name')
instructor = row.find('td', class_='actual-instructor-class').text.strip()
```

3. **Test scraping:**
```bash
python3 utils/gsu_schedule_scraper.py
```

4. **Replace demo in app.py:**
```python
# OLD (demo):
from app import generate_sample_sections
sections = generate_sample_sections(course_code)

# NEW (real):
from utils.gsu_schedule_scraper import get_real_sections
sections = get_real_sections(course_code)
```

---

## Part 2: RMP Data Updates (Already Working!)

### Current Implementation

We **already fetch from RMP** in real-time:
```python
# In utils/rmp_integration.py
rmp_data = api.get_professor_rating("John Smith", "Georgia State University")
# Returns: {rating: 4.5, difficulty: 3.2, ...}
```

This works great, but can be slow for many professors.

### Optimization: Pre-Fetch & Cache

Instead of looking up professors in real-time, **pre-fetch all GSU professors** and cache:

```bash
# Run update script (created above)
python3 scripts/update_professor_data.py
```

This creates a cached file:
```json
{
  "Robert Robinson": {
    "rating": 4.5,
    "difficulty": 3.2,
    "num_reviews": 45,
    "last_updated": "2026-01-23T16:30:00"
  },
  "Sarah Chen": {
    "rating": 4.8,
    "difficulty": 2.9,
    ...
  }
}
```

Then app.py uses cache first:
```python
# Check cache
if professor in professor_cache:
    return professor_cache[professor]
else:
    # Fetch from RMP API
    return api.get_professor_rating(professor)
```

---

## Automation Setup

### Option 1: Cron Job (Recommended for VPS/Cloud)

```bash
# Edit crontab
crontab -e

# Run daily at 2 AM
0 2 * * * cd /path/to/gsu-course-planner && python3 scripts/update_professor_data.py

# Or run hourly during registration
0 * * * * cd /path/to/gsu-course-planner && python3 scripts/update_professor_data.py
```

### Option 2: GitHub Actions (Free!)

Create `.github/workflows/update-data.yml`:
```yaml
name: Update Professor Data

on:
  schedule:
    # Run daily at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Update professor data
        run: python3 scripts/update_professor_data.py

      - name: Commit cache
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/professor_cache.json
          git commit -m "chore: Update professor data cache" || exit 0
          git push
```

### Option 3: Streamlit Cloud (For Deployed Apps)

Streamlit Cloud doesn't support scheduled jobs, but you can:

1. **Use external service:**
   - Zapier (free tier)
   - IFTTT
   - Trigger script from webhook

2. **Update on user request:**
```python
# In app.py
if st.button("🔄 Refresh Professor Data"):
    with st.spinner("Updating from RMP..."):
        update_professor_cache()
    st.success("Data refreshed!")
```

---

## Update Frequency Recommendations

### GSU Schedule Data
- **Before registration:** Daily
- **During registration:** Hourly (track seat availability)
- **After registration:** Weekly

### RMP Data
- **Daily:** During registration period
- **Weekly:** Off-season
- **Monthly:** Summer/breaks

Professors' RMP ratings don't change rapidly, so aggressive updates aren't needed.

---

## Cost & Performance

### Scraping Costs
**GSU Schedule:** FREE
- Public data
- Just be respectful (rate limit)

**RateMyProfessors:** FREE
- Public GraphQL API
- No API key required
- Rate limit: ~2 requests/second

### Performance Numbers

**Without Caching:**
- 100 professors × 0.5s = 50 seconds load time ❌

**With Caching:**
- 100 professors = instant (read from file) ✅

**Update Script:**
- 100 professors × 0.6s = 60 seconds total
- Run once daily = negligible impact

---

## Implementation Priority

### Phase 1: Get Real Sections ⭐ (Critical)
1. Inspect GSU registration site
2. Update `gsu_schedule_scraper.py` selectors
3. Test with 1-2 courses
4. Replace `generate_sample_sections()` in app.py

**Time estimate:** 2-4 hours

### Phase 2: Cache RMP Data (Optimization)
1. Run `update_professor_data.py` manually
2. Verify cache file created
3. Update app.py to check cache first
4. Test performance improvement

**Time estimate:** 1 hour

### Phase 3: Automate Updates (Polish)
1. Set up cron job or GitHub Action
2. Test automated runs
3. Monitor for errors
4. Add alerting if update fails

**Time estimate:** 1 hour

---

## Testing the Scraper

### Step 1: Manual Test
```bash
# Try scraping one course
python3 -c "
from utils.gsu_schedule_scraper import GSUScheduleScraper
scraper = GSUScheduleScraper()
sections = scraper.search_course_sections('CSC', '3320')
print(sections)
"
```

### Step 2: Verify Data Structure
```python
# Should return:
[
  {
    "section": "001",
    "crn": "12345",
    "instructor": "Robert Robinson",
    "time": "MWF 10:00-10:50",
    "location": "Room 101",
    "seats_available": "15"
  },
  ...
]
```

### Step 3: Integration Test
```python
# In app.py
from utils.gsu_schedule_scraper import get_real_sections

sections = get_real_sections("CSC 3320")
ranked = get_ranked_sections("CSC 3320", sections)

# Should now show real professors with real RMP ratings!
```

---

## Common Issues & Solutions

### Issue 1: Scraper Returns Empty List

**Cause:** HTML structure changed or incorrect selectors

**Fix:**
```bash
# Re-inspect GSU site
# Update selectors in _parse_sections()
```

### Issue 2: "Professor Not Found" in RMP

**Cause:** Name mismatch (e.g., "J. Smith" vs "John Smith")

**Fix:**
```python
# Name normalization already handles this!
# ProfessorNormalizer creates aliases
```

### Issue 3: Too Slow

**Cause:** Fetching RMP data in real-time for many professors

**Fix:**
```bash
# Use caching
python3 scripts/update_professor_data.py
```

### Issue 4: GSU Blocks Scraper

**Cause:** Too many requests too fast

**Fix:**
```python
# Increase delay in scraper
REQUEST_DELAY = 2.0  # 2 seconds between requests
```

---

## Alternative: Student Input

If scraping is too difficult, collect data from students:

```python
# In app.py
st.markdown("### 📝 Help Us Improve!")

with st.form("section_feedback"):
    course = st.text_input("Course Code", "CSC 3320")
    section = st.text_input("Section", "001")
    professor = st.text_input("Professor Name")

    if st.form_submit_button("Submit"):
        # Save to database
        save_section_data(course, section, professor)
        st.success("Thanks for contributing!")
```

Crowdsourced data can be surprisingly accurate!

---

## Legal & Ethical Notes

### ✅ Allowed:
- Scraping public GSU course schedule
- Using RMP's public API
- Caching data for your app
- Rate limiting to be respectful

### ❌ Not Allowed:
- Selling scraped data
- Claiming RMP data as your own
- Bypassing CAPTCHAs or access controls
- Ignoring robots.txt

### Best Practices:
- Add `User-Agent` header
- Respect rate limits (0.5-2s delays)
- Cache aggressively
- Give attribution (we already do!)
- Don't DoS the servers

---

## Quick Start Guide

### Get Real Sections in 30 Minutes

1. **Visit GSU registration:**
   ```
   https://registration.gsu.edu
   ```

2. **Search for CSC 3320**

3. **Right-click section table → Inspect**

4. **Find CSS selectors:**
   ```html
   <tr class="section-row">
     <td class="section-number">001</td>
     <td class="instructor-name">Dr. John Smith</td>
     ...
   </tr>
   ```

5. **Update `gsu_schedule_scraper.py` line 95:**
   ```python
   section_rows = soup.find_all('tr', class_='section-row')  # Your actual class
   instructor = row.find('td', class_='instructor-name').text
   ```

6. **Test:**
   ```bash
   python3 utils/gsu_schedule_scraper.py
   ```

7. **Replace in app.py:**
   ```python
   # Line ~720 in app.py
   # OLD:
   # sample_sections = generate_sample_sections(course_code, num_sections=4)

   # NEW:
   from utils.gsu_schedule_scraper import get_real_sections
   sample_sections = get_real_sections(course_code)
   ```

8. **Restart app:**
   ```bash
   streamlit run app.py
   ```

9. **Verify:** Should now show real professors!

---

## Summary

✅ **RMP integration already works** - we fetch ratings in real-time
✅ **What's missing:** Real professor assignments from GSU schedule
✅ **Solution:** Scrape GSU registration site
✅ **Automation:** Cron job or GitHub Actions for daily updates
✅ **Optimization:** Cache RMP data to improve performance

**Next immediate step:** Inspect GSU registration site and update scraper selectors.

---

Built with ❤️ for GSU students

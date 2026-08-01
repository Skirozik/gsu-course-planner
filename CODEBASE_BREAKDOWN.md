# PrereqPilot — Codebase Breakdown

A ground-truth description of this repository, written by reading the source rather than the
README. Every claim cites the file it came from. Counts are counted, not estimated.

Audience: an assistant writing interview prep about this project. Where the code does not
support a claim, this document says **unclear from code** instead of guessing.

Snapshot: commit `922b808`, branch `main`.

---

## 1. Stack and layout

| Layer | What it actually is | Where |
|---|---|---|
| Frontend framework | React 19 (`react ^19.2.7`, `react-dom ^19.2.7`) | `frontend/package.json` |
| Build tool | Vite 8 (`vite ^8.1.0`), plugin `@vitejs/plugin-react` | `frontend/package.json`, `frontend/vite.config.js` |
| Styling | Tailwind CSS 3 + PostCSS + autoprefixer | `frontend/tailwind.config.js`, `frontend/postcss.config.js` |
| HTTP client | axios, base URL `import.meta.env.VITE_API_URL \|\| ''` | `frontend/src/api.js` |
| Backend framework | FastAPI, served by Uvicorn | `api/main.py`, `Procfile` |
| PDF parsing | pdfplumber (primary), PyPDF2 (fallback) | `utils/academic_eval_parser.py` |
| LLM | Anthropic Python SDK | `utils/llm_integration.py` |
| Frontend hosting | Vercel — `/api/*` rewritten to the Render backend | `frontend/vercel.json` |
| Backend hosting | Render, service `prereqpilot-api`, **free plan** | `render.yaml` |

Live frontend domain is `prereqpilot.dev` (`render.yaml` `ALLOWED_ORIGINS`, and the CORS
allowlist in `api/main.py`). Backend origin is `https://multischool-course-planner.onrender.com`
(`frontend/vercel.json`). The GitHub repo is named `multischool-course-planner`
(`utils/gsu_prerequisite_parser.py` User-Agent string) — the repo name and the product name differ.

`render.yaml` sets `plan: free`, whose own comment notes the instance "sleeps after ~15 min idle".
That is a real, user-visible cold-start on the first request after idle.

### Directory tree, one line each

```
api/            FastAPI app. Single module, api/main.py — all 7 endpoints.
app.py          Legacy Streamlit prototype (1,705 lines). Not imported by api/.
utils/          All shared logic: parsers, prereq engine, Banner + RMP clients, exports.
data/           Static JSON: course catalogs, scraped prerequisites, cached section samples.
frontend/       React 19 + Vite SPA. Entry frontend/src/main.jsx -> App.jsx.
tests/          5 files; pytest collects 12 tests from 3 of them.
scripts/        Standalone maintenance scripts (professor data refresh, page inspection).
docs/           Untracked in git; contains a prior PROJECT_BREAKDOWN.md and a design guide.
.devcontainer/  VS Code dev container definition.
.streamlit/     Streamlit theme config — legacy, serves app.py only.
```

Tracked Python + JSX + JS (excluding `package-lock.json`): **12,208 lines** across 44 files.

### Streamlit is legacy — precisely what that means

`app.py` is the original Streamlit prototype: **1,705 lines**, **239 `st.*` calls**, and only
**2 top-level `def`s**, i.e. it is one long procedural script.

Two files import Streamlit (`grep -rln "import streamlit"`):

1. `app.py` — the prototype itself. Nothing in `api/` imports `app.py`.
2. `utils/llm_integration.py:14-18` — a **soft** import guarded by `try/except ImportError`
   setting `HAS_STREAMLIT`. It is used in exactly one place, `APIKeyManager.get_api_key()`
   (`utils/llm_integration.py:43-47`), which checks `st.secrets` first and falls through to
   `os.getenv`. So the live FastAPI path tolerates Streamlit being absent, but the *import
   attempt* still happens on every backend boot.

`requirements.txt` still installs `streamlit`, `pandas`, and `plotly`. `streamlit` is needed by
the legacy prototype. **`pandas` and `plotly` are referenced in zero tracked `.py` files** —
not by `api/`, not by `utils/`, not even by `app.py` (verified:
`git ls-files '*.py' | xargs grep -ln pandas` → 0 files, same for `plotly`). They are dead
dependencies installed on every Render build for nothing.

> **Stale docs note.** `README.md:62` says `npm run dev` "serves http://localhost:5173".
> `frontend/vite.config.js` sets `server.port: 3000`. The CORS allowlist in `api/main.py:32-33`
> happens to permit both, so nothing breaks — but the README states the wrong port.

> **Stale docs note.** Six files under `frontend/src/` are unused Vite scaffold left in the
> repo: `main.ts`, `counter.ts`, `style.css`, `assets/hero.png`, `assets/typescript.svg`,
> `assets/vite.svg`, plus `tsconfig.json`. `frontend/index.html:17` loads `/src/main.jsx`, and
> nothing in the React tree references `main.ts` or `counter.ts`. `hero.png` is imported only by
> the dead `main.ts:4`. **There is no product screenshot in this repository.**

---

## 2. Request flow, end to end

### 2a. Student uploads a DegreeWorks PDF

1. **Component.** `frontend/src/components/TranscriptUpload.jsx`. Uses `react-dropzone`
   (`useDropzone`, line 57) restricted to `application/pdf`, `maxFiles: 1`.
2. **Call.** `onDrop` (line 34) builds a `FormData` with field name `file` and POSTs to
   `/api/parse-transcript?school=<school>` with `Content-Type: multipart/form-data` (lines 42-46).
   The school is a **query-string** parameter, not part of the body.
3. **Endpoint.** `api/main.py:135` `async def parse_transcript(school: str, file: UploadFile)`.
   Guarded by the `rate_limit` dependency. Rejects any filename not ending `.pdf` with 400
   (line 137) — an extension check, not a content check.
4. **Dispatch.** `api/main.py:143-146`: if `school == "Georgia Tech"` →
   `parse_gatech_degreeworks(content)` (`utils/gatech_parser.py`), else
   `parse_academic_eval(content)` (`utils/academic_eval_parser.py`). The GSU parser is the
   default for any unrecognized school string.
5. **Text extraction.** `utils/academic_eval_parser.py:113` `_extract_text` opens the bytes with
   `pdfplumber` at `x_tolerance=3, y_tolerance=3` (line 123); on exception it falls back to
   `PyPDF2` (line 132); if neither library is importable it raises `RuntimeError` (line 139).
6. **Parse.** `parse_academic_eval` (line 30) returns a dict assembled from five private helpers:
   `_parse_student_info`, `_parse_completed_courses`, `_parse_in_progress_courses`,
   `_parse_required_courses`, `_parse_requirements_summary`. All five are regex over the flat
   extracted text — there is no PDF layout/table analysis.

**Parsed shape** (the literal return of `parse_academic_eval`, lines 30-39):

```python
{
  "student_info": {          # _parse_student_info, line 146
     "student_name", "student_id", "gpa", "major", "college", "degree",
     "credits_required" (default 120), "credits_applied" (default 0),
     "catalog_year", "academic_standing", "advisor"
  },
  "completed_courses":   [{"course_code","course_name","grade","credits","term"}],
  "in_progress_courses": [{"course_code","course_name","credits","term"}],
  "required_courses":    [{"credits","courses":[...],"is_choice","requirement_type", ...}],
  "requirements_summary": {"degree_name","total_credits_required",
                           "total_credits_completed","sections":[...]}
}
```

The completed-course regex is `_COURSE_RE` (`utils/academic_eval_parser.py:254-261`), a
six-group pattern: dept, number, name, grade, credits, term. Grades in
`_SKIP_GRADES = {"NA","IP","W","-W"}` are dropped (line 270). Duplicate course codes are
deduped keeping the **better** grade via `_GRADE_ORDER` (lines 263-269, 296-299) — this is the
retake-handling behavior.

7. **Normalization for the wire.** `api/main.py:115` `normalize_eval_data` flattens
   `student_info` up to the top level and renames `credits_applied` → `total_credits`. It
   deliberately drops `raw_text` (comment, line 131). Response is
   `{"success": true, "data": {...}}` (line 147).
8. **Next.** `TranscriptUpload.jsx:47` calls `onUpload(data.data)`, which is
   `App.jsx:25 handleTranscript` → stores in `evalData` state → advances `step` to `'prefs'`.

Failure mode: any parser exception becomes a 422 whose `detail` embeds `str(e)`
(`api/main.py:148-149`), surfaced verbatim in the UI (`TranscriptUpload.jsx:51`).

### 2b. Student generates a schedule

1. **Component.** `frontend/src/components/PreferencesForm.jsx`. `handleSubmit` (line 21) POSTs
   to `/api/recommendations` with `{eval_data, school, career_goals, max_courses, has_job}`
   (lines 26-31). Note it does **not** send `major`.
2. **Endpoint.** `api/main.py:152` `get_recommendations(req: PreferencesRequest)`. Requires an
   API key or returns 503 (lines 154-156).
3. **Build the taken-set.** Lines 159-160: completed course codes **plus** in-progress codes.
   In-progress counts as taken (comment, line 199).
4. **Pick a catalog.** Line 164-165: `major = req.major or eval_data.get("major","")`. Since the
   frontend never sends `major`, this is entirely whatever the PDF parser extracted. If it is
   empty, `catalog` is `None`.
5. **Filter to eligible courses.** Lines 167-183. Either branch calls
   `check_prerequisites_met(code, set(completed))` — the **flat** function from
   `utils/prerequisites.py:395`, not the resolver (see §3). Result truncated to 20
   (line 185).
6. **LLM call.** `CourseRecommender(api_key).generate_schedule(...)` (lines 204-210).
7. **Response.** `{"success": True, "recommendations": result, "available_courses": [...]}`
   (line 211) → `onResults(data)` → `App.jsx:30` → `Results.jsx`.

**After results render**, `Results.jsx` makes four further calls, all lazily and per user action:

- `/api/sections` — `Results.jsx:194`, fired inside `CourseCard.toggle()` (line 187), i.e. one
  request **per course card the user expands**, cached in component state so re-collapsing does
  not refetch.
- `/api/chat` — `Results.jsx:38`.
- `/api/plan-feedback` — `Results.jsx:342`.
- `/api/export` — `Results.jsx:371`, `responseType: 'blob'`, triggers a download via a synthetic
  `<a>` element (lines 376-383). Export failures are swallowed silently (line 384-386, with a
  comment saying so).

---

## 3. The prerequisite engine

This is the most interesting part of the codebase and also the part where the honest story is
most different from the marketing. **There are three separate prerequisite implementations, and
the most sophisticated one is not on the live request path.**

### The three implementations

| # | File | Entry point | Data source | Reached by the API? |
|---|---|---|---|---|
| 1 | `utils/prerequisites.py` (558 lines) | `check_prerequisites_met` (line 395) | hardcoded `COURSE_DATABASE` dict | **Yes** — `api/main.py:19,170,178` |
| 2 | `utils/prerequisite_resolver.py` (412 lines) | `PrerequisiteResolver.evaluate_eligibility` (line 158) | free-text `prerequisites_raw` | Only via `catalog_loader`, which the API does not call for this |
| 3 | `utils/academic_eval_parser.py` | `get_next_semester_recommendations` (line 42) | hardcoded 18-entry dict (lines 51-73) | **No** — imported at `api/main.py:15` but never called |

#### Implementation 1 — what actually runs

`check_prerequisites_met(course_code, completed_courses)` (`utils/prerequisites.py:395-418`) is a
flat set-membership check. It calls `get_prerequisites` (line 347), which is a plain
`COURSE_DATABASE.get(code, {}).get("prerequisites", [])`. There is no grade logic, no OR logic,
no recursion. `min_grade` **is stored** on every `COURSE_DATABASE` entry but this function never
reads it.

`COURSE_DATABASE` holds **40 courses** (counted). `data/course_catalogs/cs_major.json` holds
**64**. **34 of those 64 are absent from `COURSE_DATABASE`** — e.g. `CSC 2510`, `CSC 4110`,
`CSC 4120`, `CSC 4220`. For every one of them `get_prerequisites` returns `[]`, so
`check_prerequisites_met` returns `can_take: True` unconditionally. **A course the student is
not eligible for is offered to the LLM as available, purely because it is missing from a
hardcoded dict.** This is the single most important correctness caveat in the project.

#### Implementation 2 — the real engine (the interview centerpiece)

`utils/prerequisite_resolver.py`, 412 lines. Turns catalog free text into a structure, then
evaluates it.

**The intermediate representation.** Two dataclasses, both at the top of the file:

```python
@dataclass                                    # line 19
class PrerequisiteRequirement:
    course_code: str
    min_grade: Optional[str] = "D"            # default floor

@dataclass                                    # line 31
class PrerequisiteGroup:
    requirements: List[PrerequisiteRequirement]
    logic: str = "AND"                        # "AND" or "OR"
```

So the parsed form of a prerequisite string is `List[PrerequisiteGroup]` — a flat list of
groups, where **groups are implicitly ANDed together** (explicit comment,
`prerequisite_resolver.py:219`) and each group is internally either all-AND or all-OR.

**Free text → structure**, `parse_prerequisites` (line 60):

1. **Lift the grade out first** (lines 82-83). One regex,
   `with\s+(?:a\s+)?(?:grade\s+of\s+)?([A-DF][+-]?)\s+or\s+(?:higher|better)`, scans the *whole*
   string; the first hit becomes `min_grade` for **every** requirement produced. Default `"D"`.
2. **Strip** the grade clause and common tails — `"Students must meet..."`,
   `"or permission of..."` (lines 86-91).
3. **Split on parentheses** (lines 96-116). Each `(...)` becomes one group via
   `_parse_course_group`. The parenthetical text is then removed, remaining `" and "` is
   collapsed to a space, and whatever is left becomes one final group.
4. **`_parse_course_group`** (line 125) decides logic by a single test: if the group text
   contains `\s+or\s+` the whole group is `OR`, otherwise `AND` (lines 135-136). Course codes are
   harvested with `r'\b([A-Za-z]{2,4})\s+(\d{4}[A-Za-z]?)\b'` (line 142) and upper-cased.

Worked example — `"(CSC 2720 or DSCI 2720) and either MATH 3020 or MATH 3030 with a C or higher"`
(this exact string is in the docstring at line 66) parses to:

```python
[ PrerequisiteGroup([CSC 2720 (min C), DSCI 2720 (min C)], logic="OR"),
  PrerequisiteGroup([MATH 3020 (min C), MATH 3030 (min C)], logic="OR") ]
```

Both groups OR-internally, ANDed with each other. Correct for this input.

**Known limits of this representation, visible in the code:**

- **No nesting.** `paren_pattern = r'\(([^)]+)\)'` (line 96) cannot match nested parentheses, and
  `PrerequisiteGroup` cannot contain another group. `"(A and (B or C))"` is not expressible.
- **One grade for everything.** `"CSC 1301 with a B or higher and MATH 1113 with a C or higher"`
  yields `min_grade="B"` for *both* courses — the first match wins and is broadcast.
- **`AND` is inferred from absence.** A group with neither "and" nor "or" is labelled `AND`;
  a comma-separated list `"CSC 2720, CSC 3210, and CSC 3320"` becomes one AND group only because
  it contains no `" or "`.
- The word `either` is not consumed by any rule — it survives into `_parse_course_group` and is
  simply ignored by the course-code regex.

**The 13-level grade ladder**, `GRADE_VALUES` (`prerequisite_resolver.py:49-55`):

```python
'A+':13, 'A':12, 'A-':11, 'B+':10, 'B':9, 'B-':8,
'C+':7,  'C':6,  'C-':5,  'D+':4,  'D':3, 'D-':2, 'F':1
```

Comparison is `_meets_grade_requirement` (line 274): `GRADE_VALUES.get(earned,0) >=
GRADE_VALUES.get(required,0)`. The `0` default is significant — **any grade not in the table
scores 0 and therefore fails every requirement**, including `"W"`, `"T"`/`"TR"` (transfer
credit), `"IP"`, and `"P"` (pass). A transferred course counts as not-passed on this path.

The same ladder is duplicated as `_GRADE_ORDER` in `utils/academic_eval_parser.py:263-269` with
identical values, used there for retake dedup. Two copies, no shared constant.

**Eligibility resolution**, `evaluate_eligibility` (line 158):

1. Parse to groups; if none, return `eligible: True, reason: "No prerequisites required"`
   (lines 185-191).
2. Build `transcript: Dict[code, grade]` from the completed list, defaulting a missing grade to
   `"F"` (line 197).
3. `_evaluate_group` (line 237) sorts each requirement into met/missing. Three cases (lines
   256-270): in transcript and grade passes → met; in transcript but grade too low → **missing**;
   in `in_progress` → **missing**, with the explicit comment "can't use as prereq yet" (line 266);
   absent → missing.
4. Per-group satisfaction (lines 212-215): `AND` needs `len(missing)==0`; `OR` needs
   `len(met)>0`.
5. `eligible = all(group_results)` (line 220).

**Chain resolution is not implemented here.** `get_missing_prerequisites_detail` (line 314)
accepts a `catalog_loader` argument and is documented to return prerequisites-of-prerequisites,
but the loop at lines 349-359 appends `"sub_prerequisites": []` with the inline comment
`# Would be populated recursively`. It is a stub. Actual recursive chain walking exists only over
the *hardcoded* dicts: `utils/prerequisites.py:365 get_all_prerequisites` and
`utils/catalog_loader.py:309`, both cycle-guarded by a `visited` set.

#### How implementation 2 is (barely) reached

`utils/catalog_loader.py` is the only caller. Two paths:

- `check_prerequisites_met` (line 238) — falls back to the resolver **only when** a catalog
  course has an empty structured `prerequisites` list but a non-empty `prerequisites_raw`
  (lines 264-273). It then fabricates grades: `{"course_code": c, "grade": "A"}` for every
  completed course (line 271, comment "No grades available on this path; assume completed
  courses passed"). So on this path the grade ladder is present but inert.
- `check_prerequisites_with_grades` (line 430) and `get_eligible_courses_with_grades` (line 502)
  — the genuinely grade-aware entry points. **Neither is called anywhere outside
  `catalog_loader.py` itself** (verified by grep across all tracked `.py`). The only reference is
  the internal call at line 541.

`api/main.py` uses `catalog_loader` exactly once, at line 165, and only to fetch the raw catalog
dict — never to evaluate eligibility.

**Net:** the 13-level ladder, the OR logic, and the in-progress rule are all real, all tested,
and all bypassed by the live `/api/recommendations` path.

#### Where the free text comes from

`utils/gsu_prerequisite_parser.py` (370 lines) scrapes `catalogs.gsu.edu` (Modern Campus),
`CATALOG_ID = "42"` for 2025-2026 (line 49), 1 req/sec (`REQUEST_DELAY = 1.0`, line 57), with a
self-identifying User-Agent (lines 52-54). `parse_course_detail` (line 150) anchors on
`<h1 id="course_preview_title">` then regexes the flattened page text for
`Prerequisite(s):`, `Corequisite(s):`, `Requirements:`/`Restrictions:` (lines 210-256), keeping
the text **exactly as written** into the `CourseData` dataclass (line 24).

Output lives at `data/parsed_prerequisites/csc_prerequisites_catalog_38.json`: **52 course
entries, 51 with non-empty `prerequisites_raw`** (counted). Note the filename says catalog 38
while the class default is 42, and `main()` at line 341 instantiates `catalog_id="38"` — the
committed data is from the older catalog.

---

## 4. External integrations

### 4a. Banner session/term handshake

Implemented in `utils/gsu_banner_api.py` (442 lines) and `utils/gatech_banner_api.py` (442 lines).

Endpoints (`gsu_banner_api.py:26-33`):

```
BASE_URL        https://registration.gosolar.gsu.edu/StudentRegistrationSsb
TERM_SELECTION  {BASE}/ssb/term/search?mode=search
RESULTS         {BASE}/ssb/searchResults/searchResults
FACULTY_TIMES   {BASE}/ssb/searchResults/getFacultyMeetingTimes
```

`SEARCH_ENDPOINT` and `SECTION_DETAILS` are defined (lines 30, 32) but never called.

**Order of calls**, `search_courses` (line 117):

1. `select_term(term)` (line 76) — `POST` to `TERM_SELECTION`, form-encoded
   `{term, studyPath, studyPathText, startDatepicker, endDatepicker}`. Returns `True` on HTTP 200.
   If it returns `False`, `search_courses` aborts and returns `[]` (lines 137-139).
2. `POST` to `RESULTS_ENDPOINT` with `{txt_term, txt_subject, pageOffset, pageMaxSize,
   sortColumn, sortDirection}` (lines 142-149), then `data["data"]` out of the JSON (line 172).

**Cookies.** Carried implicitly. `__init__` (line 42) creates a `requests.Session()`; the
`JSESSIONID` Banner sets during term selection rides along on the results POST via the session's
cookie jar. Nothing in the code names or inspects a cookie — the handshake works because the two
POSTs share one `Session`. This is why step 1 is mandatory and why a fresh `GSUBannerAPI()` per
request (which is what `api/main.py:305,315-317` does) pays the handshake every time.

`X-Requested-With: XMLHttpRequest` is set in `HEADERS` (line 39) with the comment "Important for
AJAX calls", alongside a spoofed browser User-Agent (line 36).

**Term codes.** `get_current_term` (line 54) is pure local-clock arithmetic: month ≤ 5 → `01`
(Spring), ≤ 7 → `05` (Summer), else `08` (Fall), formatted `f"{year}{term_code}"`. There is no
validation that the computed term exists in Banner. Running in, say, November yields the *current*
Fall term rather than the Spring term a student would actually be registering for.

**The two adapters are copy-paste.** `diff utils/gsu_banner_api.py utils/gatech_banner_api.py`
reports **56 differing lines out of 442**, and the differences are: docstrings, class name
(`GSUBannerAPI` → `GATechBannerAPI`), `BASE_URL`, the default `subject` (`"CSC"` → `"CS"`), and
the module-level function name (`get_gsu_sections` → `get_gatech_sections`). `extract_section_data`,
`get_current_term`, `select_term`, `search_courses`, and the rate limiter are byte-identical.

### 4b. What the normalization layer unifies

There is no separate normalization module. Unification happens because both adapters implement
an identical `extract_section_data` (`gsu_banner_api.py:225`) that flattens Banner's nested
response into one flat dict:

```python
{"section","crn","instructor","course_code","course_title","time","days","location",
 "seats_available","seats_total","waitlist_available","credits","campus",
 "instructional_method","term"}
```

Specifically it collapses `faculty[0].displayName` → `instructor` (defaulting `"Staff"`, and
mapping `"TBA"` → `"Staff"`, lines 236-242), and `meetingsFaculty[0].meetingTime` → `time`,
`days`, `location`, building the day string from seven boolean fields (lines 262-270). Only the
**first** faculty member and the **first** meeting block survive; multi-instructor and
split-schedule sections lose data.

`api/main.py:314-317` picks the adapter by `"tech" in school.lower()`, and downstream
`get_ranked_sections` consumes the flat shape without knowing which school produced it.

Course filtering is exact, not substring: `_norm` strips whitespace and upper-cases, then compares
full codes (`gsu_banner_api.py:363-370`) — with a comment explaining that a substring match would
wrongly match `CSC 3320` for `CSC 320`.

### 4c. Rate My Professors

`utils/rmp_integration.py` (449 lines). `POST https://www.ratemyprofessors.com/graphql`
(line 28) with a hardcoded header `Authorization: Basic dGVzdDp0ZXN0` (line 37) — that decodes to
`test:test`, RMP's well-known public token. School IDs are hardcoded base64 (lines 31-32):
`U2Nob29sLTM2MA==` → `School-360` (GSU), `U2Nob29sLTM2MQ==` → `School-361` (Georgia Tech).

One query, `NewSearchTeachersQuery` (lines 113-132), selecting
`id, firstName, lastName, avgRating, avgDifficulty, numRatings, wouldTakeAgainPercent,
department`.

**Match selection** (lines 162-173): tokenize the query name, score each candidate by
`(count of query tokens appearing in "first last", numRatings)`, take the `max`. So token overlap
dominates and review count breaks ties.

> **Stale docs note.** The docstring at line 98-100 says it "Picks the result whose **last name**
> best matches the query… Falls back to the highest-rated result". Neither is what the code does:
> `match_score` (line 164) checks tokens against the **full** name, not the last name, and the
> tiebreak is `numRatings` (most-rated), not `avgRating` (highest-rated).

**Ranking score**, `SectionRanker.compute_score` (`utils/professor_ranking.py:273-305`):

```
score = (rating * 20) + min(numReviews, 50) - (difficulty * 2)
```

Weights are class constants at lines 269-271 (`RATING_WEIGHT=20.0`, `DIFFICULTY_WEIGHT=-2.0`,
`REVIEW_CAP=50`). No RMP data → score `0.0` (line 292), which sorts last. The module docstring
(line 5) is explicit that this is "an ADVISORY system only - it ranks options but never blocks
sections", and nothing in the code filters a section out on rating.

Sort is `rank_sections` (line 308): descending by `(score, num_reviews, -difficulty, section)`.
Note the fourth key inherits `reverse=True`, so a genuine all-else-equal tie orders section
`"003"` before `"001"` — cosmetic, not a correctness issue.

### 4d. Disk cache

| Property | Value | Source |
|---|---|---|
| Location | `data/rmp_cache.json`, resolved relative to the module file | `rmp_integration.py:50` |
| Key | `f"{school_id}\|{name.strip().lower()}"` | `_cache_key`, line 55-57 |
| Load | whole file into a dict at `__init__` | `_load_persistent_cache`, line 59 |
| Write | whole file rewritten after **every** successful lookup | `_save_persistent_cache`, line 69, called at line 186 |
| Invalidation | **none** | no TTL, no version, no eviction anywhere in the file |

Two real consequences visible in the code:

- **Negative results are never cached.** The `if not edges: return None` path (lines 154-156) and
  the exception path (lines 189-191) both return without touching `_persistent_cache`. Only the
  success path at line 185 writes. So every professor RMP has never heard of costs a fresh
  network round-trip — plus the 0.5 s `REQUEST_DELAY` (line 40) — on every single request.
- **Cache never goes stale, ever.** A professor's rating is frozen at first fetch for the life of
  the file. `data/rmp_cache.json` is gitignored (`.gitignore`) so it is empty on a fresh Render
  boot and rebuilt from zero; on Render's ephemeral filesystem it also does not survive a redeploy.

`cache_stats()` (line 78) reports `{total, with_rating}` but is not called from `api/` or
`frontend/`.

> **Stale docs note.** `utils/section_recommender.py:81-82` says "The lookups are lru_cached, so
> repeated courses… reuse the cached result". There is **no `functools.lru_cache` anywhere in
> `utils/`** — grep returns only two comments *mentioning* it (this one and
> `rmp_integration.py:48`). The actual mechanism is the disk-backed dict above. The behavior the
> comment claims is roughly delivered, but by a different mechanism, and the de-duplication it
> describes is really done by the explicit `seen` set at `section_recommender.py:84-94`.

---

## 5. The Claude integration

Three separate call sites, three different configurations. There is no shared client.

| Call site | Model | Max tokens | Temperature |
|---|---|---|---|
| `CourseRecommender` (`utils/llm_integration.py:81-82`) | `claude-sonnet-4-6`, falling back to `claude-haiku-4-5-20251001` | 1500 (line 83) | 0.7 (line 84) |
| `/api/chat` (`api/main.py:248`) | `claude-haiku-4-5-20251001` | 512 | default |
| `/api/plan-feedback` (`api/main.py:393`) | `claude-sonnet-4-6` | 600 | default |

`/api/chat` and `/api/plan-feedback` each construct their own `Anthropic(api_key=...)` **inside
the request handler** (`api/main.py:224-225`, `358-359`) — a new client per request.

**Key resolution.** `APIKeyManager.get_api_key` (`utils/llm_integration.py:33-55`): Streamlit
secrets → `os.getenv("ANTHROPIC_API_KEY")` → `None`. `validate_api_key` (line 58) checks the key
starts with `sk-` and is ≥ 20 chars.

**Where the prompt is built.** `CourseRecommender._build_prompt`
(`utils/llm_integration.py:204-257`). It assembles four sections — STUDENT, PREFERENCES,
AVAILABLE COURSES, REQUIREMENTS — from three formatters that all silently truncate:
`_format_completed_courses` keeps **8** courses (line 264), `_format_available_courses` keeps
**15** (line 272), `_format_requirements` keeps **8** (line 284). The endpoint has already capped
`available_courses` at 20 (`api/main.py:185`), so up to 5 eligible courses are dropped again here
without any signal.

The system prompt is a constant (lines 85-88): *"You are an academic advisor. Respond with valid
JSON only — no prose, no explanations, and no markdown code fences."*

**The schema it is constrained to.** It is **not** constrained — there is no tool-use, no
`response_format`, no JSON mode. The schema is a literal example embedded in the user prompt
(`llm_integration.py:243-252`):

```json
{ "recommended_courses": [ {"course_code":"...","course_name":"...","reason":"...",
                            "difficulty":"Easy/Medium/Hard"} ],
  "reasoning": "Brief explanation", "difficulty_balance": "Light/Balanced/Challenging",
  "semesters_remaining": 3, "alternatives": [] }
```

Line 241 adds the anti-hallucination instruction: *"Use the EXACT course codes and course names
from the AVAILABLE COURSES list above. Do NOT make up or guess course names."* — prompt-level
only; nothing verifies it afterwards.

**The validation path, quoted in full** (`utils/llm_integration.py:291-316`):

```python
def _parse_response(self, response_text: str) -> Dict:
    """Parse the Claude response and extract JSON"""
    try:
        json_str = response_text

        # Remove markdown code blocks
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0]

        data = json.loads(json_str.strip())

        # Validate structure
        if "recommended_courses" in data:
            logger.info("✅ Parsed response successfully")
            return data
        else:
            return self._get_error_response("Invalid response structure")

    except json.JSONDecodeError as e:
        logger.error(f"JSON error: {e}")
        return self._get_error_response(f"Parse error: {str(e)[:50]}")
```

That is the entire contract between model output and the UI: strip fences, `json.loads`, and
check that **one key exists**. Not validated: that `recommended_courses` is a list; that its
elements are objects; that `course_code` is present, well-formed, or corresponds to any real
course; that the returned courses came from the AVAILABLE list; that `difficulty` is one of the
three advertised values. `Results.jsx` renders `course.course_code` and `course.difficulty`
(lines 214, 216) straight from this. **A hallucinated course code reaches the user unchallenged**,
and `/api/sections` will then simply return `{"sections": []}` for it.

On any failure `_get_error_response` (line 318) returns a **200-shaped success object** with an
empty `recommended_courses` and `reasoning` set to `"❌ <message>"` (line 323). The frontend has
no way to distinguish "no courses recommended" from "the model call failed" other than reading
that emoji.

**Fallback loop.** `_call_api` (line 176) iterates `[sonnet, haiku]`. `AuthenticationError` and
`RateLimitError` re-raise immediately (lines 195-197, correctly — switching models cannot fix
them); everything else logs a warning and tries the next model. Per-call `timeout=30` (line 187).

> **Stale docs note.** `api/main.py:193` reads `eval_data.get("degree_requirements", {})` and
> passes it to `generate_schedule`. But `normalize_eval_data` (line 115-132) — the function that
> produces the very dict the frontend sends back — **never emits a `degree_requirements` key**. It
> emits `required_courses` and `requirements_summary`. So `degree_requirements` is **always empty**,
> `_format_requirements` always hits its empty branch, and the prompt's REQUIREMENTS section
> always literally reads `"No requirements"`. The degree-requirements feature is wired but dead.

---

## 6. API surface

**7 endpoints**, all in `api/main.py` (counted: `grep -cE '^@app\.(get|post|put|delete|patch)'`).
All except `/api/health` carry `dependencies=[Depends(rate_limit)]`.

| # | Method | Path | Takes | Returns | Line |
|---|---|---|---|---|---|
| 1 | GET | `/api/health` | — | `{status, has_api_key}`; used as Render's `healthCheckPath` | 109 |
| 2 | POST | `/api/parse-transcript` | `school` (query), `file` (multipart PDF) | `{success, data}` — normalized transcript; 400 non-PDF, 422 parse failure | 135 |
| 3 | POST | `/api/recommendations` | `PreferencesRequest` | `{success, recommendations, available_courses}`; 503 if no API key | 152 |
| 4 | POST | `/api/chat` | `ChatRequest` (`messages`, `context`) | `{reply}` — advisor chat, Haiku, 512 tokens | 218 |
| 5 | POST | `/api/export` | `ExportRequest` (`courses`, `student_info`, `format`) | binary `pdf` / `ics` / `txt` with `Content-Disposition`; 400 empty or unknown format | 263 |
| 6 | GET | `/api/sections` | `course`, `school` (query) | `{course, sections[]}` — live Banner sections RMP-ranked; 502 if Banner unreachable | 302 |
| 7 | POST | `/api/plan-feedback` | `PlanFeedbackRequest` (`courses`, `student`, `school`) | `{feedback}` — 3-5 sentence critique, Sonnet | 350 |

Cross-cutting: CORS allowlist from `ALLOWED_ORIGINS` env or a 4-entry default (lines 29-46);
a catch-all `@app.exception_handler(Exception)` that logs the traceback server-side and returns a
generic `{"detail": "Internal server error"}` (lines 83-87).

---

## 7. What changed in the rewrite

**Survived from the Streamlit prototype — reused verbatim by the FastAPI app:**

- The DegreeWorks parsers. `utils/academic_eval_parser.py` and `utils/gatech_parser.py` are
  imported by both `app.py:7` and `api/main.py:15-16`.
- The prerequisite engine, all three implementations (`utils/prerequisites.py`,
  `utils/prerequisite_resolver.py`, `utils/catalog_loader.py`).
- Both Banner clients, the RMP client, `professor_ranking`, `section_recommender`, `export_utils`.
- `utils/llm_integration.py` — still carries its Streamlit-secrets branch (lines 14-18, 43-47),
  which is the clearest fossil of the prototype in live code.

In short: **the entire `utils/` layer survived.** The rewrite was a UI and transport change, not
an engine change.

**Rebuilt from scratch:**

- `api/main.py` (399 lines) — new FastAPI transport layer, plus things the prototype never had:
  the sliding-window rate limiter (lines 56-80), the CORS allowlist (29-46), the global exception
  handler (83-87), and `normalize_eval_data` (115) as an explicit wire format.
- The whole `frontend/` React SPA — 6 components, a 5-state `step` machine in `App.jsx:10`.
- Deployment: `render.yaml`, `frontend/vercel.json`, `Procfile`, `railway.json`.

**Regressed or not yet ported — this is where the rewrite lost ground:**

1. **Eligibility got dumber.** `app.py:1224` calls `catalog_loader.check_prerequisites_met`, the
   catalog-aware method that can fall through to the text resolver. `api/main.py:170` calls the
   flat `utils/prerequisites.check_prerequisites_met` against a 40-course hardcoded dict. The
   React app evaluates prerequisites *less* accurately than the Streamlit prototype did.
2. **Degree-requirements context lost.** Dead `degree_requirements` key, §5 — the prototype fed
   `get_next_semester_recommendations` (`app.py:720`); the API imports that function
   (`api/main.py:15`) and never calls it.
3. **Streamlit-only features not ported.** `app.py` calls `get_degree_progress` (line 1144),
   `get_core_courses` (1181), `get_elective_courses` (1213), `get_math_requirements` (1233), and a
   whole catalog-explorer UI (1275-1334). None have endpoints in `api/main.py`.
4. **`generate_sample_sections` still exists** at `app.py:33`, despite
   `gsu_banner_api.py:336` claiming "This REPLACES generate_sample_sections() in app.py". It was
   replaced on the API path only.

---

## 8. Honest edges

Things a sharp interviewer would find. Each is a real, located defect.

**Correctness**

1. **The 34-course eligibility hole** (§3). Any catalog course missing from the 40-entry
   `COURSE_DATABASE` is reported eligible unconditionally. This is the headline bug.
2. **`degree_requirements` is always `{}`** (`api/main.py:193` vs `normalize_eval_data`, line 115).
   The LLM never sees degree requirements.
3. **Unvalidated model output** (`llm_integration.py:305`). One `in` check. Hallucinated course
   codes render.
4. **Transfer and pass grades fail every prerequisite.** `GRADE_VALUES.get(grade, 0)`
   (`prerequisite_resolver.py:285`) returns 0 for `T`, `TR`, `IP`, `P`, `W`. Meanwhile
   `_COURSE_RE` (`academic_eval_parser.py:258`) *does* capture `T`/`TR` as valid grades, so a
   transfer course enters the transcript and then silently fails eligibility.
5. **Errors are laundered into successes.** `_get_error_response` (`llm_integration.py:318`)
   returns a valid-shaped payload; `/api/recommendations` wraps it in `{"success": True}`
   (`api/main.py:211`). An API failure is indistinguishable from an empty recommendation.
6. **Term codes are guessed from the local clock** (`gsu_banner_api.py:54-74`) with no validation
   against Banner's actual term list. Wrong half the year for registration purposes.
7. **`min_grade` in `COURSE_DATABASE` is never read.** Every entry has one
   (`prerequisites.py:18` etc.), and the only consumer, `check_prerequisites_met`, ignores it.

**Missing error handling**

8. **The advertised 10 MB limit does not exist.** `TranscriptUpload.jsx:133` renders
   "PDF only · Max 10 MB". `useDropzone` (line 57) sets no `maxSize`, and `parse_transcript`
   (`api/main.py:136-140`) does `await file.read()` — the **entire** upload into memory — after
   checking only the filename extension. A large or non-PDF-but-`.pdf`-named file is read in full
   before anything validates it.
9. **Export failures are silent** (`Results.jsx:384-386`, with a comment acknowledging it).
10. **Bare `except:`** in `generate_rmp_url` (`professor_ranking.py:43`) swallows everything
    including `KeyboardInterrupt`.
11. `_fill_missing_names_from_banner` (`academic_eval_parser.py:461`) wraps its entire body in
    `try/except Exception: pass` (line 489) — a live Banner call that fails invisibly.

**Concurrency and load**

12. **The rate limiter leaks memory.** `_rate_hits: defaultdict(deque)` (`api/main.py:58`) is
    keyed by client IP and **never evicted** — only individual timestamps are popped (lines 72-73).
    One deque per unique IP accumulates for the process lifetime.
13. **The rate limiter is per-process** — its own comment says so (`api/main.py:54`). Correct on
    Render's single free instance; silently multiplies the effective limit by N on any scale-out.
14. **The rate limiter is not thread-safe.** FastAPI runs sync `def` endpoints in a threadpool;
    the check-then-append at lines 75-80 is a read-modify-write on shared state with no lock.
    Benign in effect (an occasional extra request slips through), but it is a genuine race.
15. **RMP cache writes are a read-modify-write on a whole file** with no lock
    (`rmp_integration.py:69-76`), called on every successful lookup (line 186). Two concurrent
    `/api/sections` requests can interleave and lose entries, or leave a torn file — which the
    loader then discards wholesale on `JSONDecodeError` (line 65).
16. **`/api/sections` is unbounded fan-out.** One request → a fresh Banner session (term POST +
    search POST) → then one RMP HTTP call per unique instructor, each serialized behind a 0.5 s
    `REQUEST_DELAY` (`rmp_integration.py:40,87-92`). A 10-instructor course blocks a worker for
    ≥ 5 s, and a cache miss on an unknown professor is never cached (§4d), so it never gets faster.
17. **Cold start.** Render free plan sleeps (`render.yaml`); the first upload after idle waits on
    a full container boot.

**Not-really-secrets, but worth naming**

18. Two credentials are hardcoded and committed: the RMP `Basic dGVzdDp0ZXN0` token
    (`rmp_integration.py:37`) and the spoofed browser User-Agents in both Banner clients
    (`gsu_banner_api.py:36`). Neither is a private secret — the RMP token is public and
    well-known — but both are third-party access patterns that could break or be blocked without
    notice, and the scraping depends on them.

**What has no tests**

`pytest tests/` collects **12 tests** and **all 12 pass** (verified). Coverage by file:

| Area | Tests? |
|---|---|
| `utils/prerequisite_resolver.py` | ✅ 6 tests (`tests/test_prerequisite_resolver.py`) — the only well-covered module |
| `utils/professor_ranking.py` / `section_recommender.py` | ✅ 5 tests (`tests/test_section_ranking.py`) |
| `utils/gsu_prerequisite_parser.py` | ⚠️ 1 test (`tests/test_prerequisite_parser.py`) — and it `return`s a bool instead of asserting, which pytest warns about (`PytestReturnNotNoneWarning`) |
| **`api/main.py` — all 7 endpoints** | ❌ **none** |
| **`utils/academic_eval_parser.py`** (the PDF parser) | ❌ **none** |
| **`utils/gatech_parser.py`** | ❌ **none** |
| **`utils/llm_integration.py`** (incl. `_parse_response`) | ❌ **none** |
| **`utils/prerequisites.py`** (the code that actually runs) | ❌ **none** |
| **Both Banner clients** | ❌ **none** |
| **`utils/rmp_integration.py`** | ❌ **none** |
| **`utils/catalog_loader.py`** | ❌ **none** |
| **Frontend (all 6 components)** | ❌ none — no test runner in `frontend/package.json` |

Two files in `tests/` — `test_major_requirements_parser.py` and `test_rmp_export.py` — contain no
`test_`-prefixed functions and pytest collects **0** from them; they are runnable scripts, not tests.

The sharpest version of this: **the two modules on the live critical path with zero tests are the
PDF parser and the eligibility check that the API actually calls.** The thoroughly tested resolver
is the one the API bypasses.

---

## 9. Numbers worth quoting

Every figure below is counted from the code or data in this repo.

| Metric | Value | How it was counted |
|---|---|---|
| FastAPI endpoints | **7** | `grep -cE '^@app\.(get\|post\|put\|delete\|patch)' api/main.py` |
| React components | **6** | `frontend/src/components/*.jsx` (+ `App.jsx`, `main.jsx`) |
| Tests collected / passing | **12 / 12** | `pytest tests/ -q` |
| Test files that collect nothing | **2 of 5** | `pytest --collect-only` |
| Prereq engine — resolver | **412 lines** | `utils/prerequisite_resolver.py` |
| Prereq engine — hardcoded DB | **558 lines**, **40 courses** | `utils/prerequisites.py` |
| Prereq engine — catalog scraper | **370 lines** | `utils/gsu_prerequisite_parser.py` |
| Grade ladder levels | **13** (A+ = 13 → F = 1) | `prerequisite_resolver.py:49-55` |
| Courses across all catalogs | **145** | 6 files in `data/course_catalogs/` |
| Largest single catalog | **64** (`cs_major.json`) | same |
| Catalog courses with no prereq data in `COURSE_DATABASE` | **34 of 64** | set difference, §3 |
| Scraped CSC courses | **52**, of which **51** have prerequisite text | `data/parsed_prerequisites/csc_prerequisites_catalog_38.json` |
| Cached section fixtures | **12** GSU, **31** Georgia Tech | `data/gsu_sections_real.json`, `data/gatech_sections_real.json` |
| Banner adapter duplication | **56 differing lines of 442** (~87% identical) | `diff utils/gsu_banner_api.py utils/gatech_banner_api.py` |
| Legacy Streamlit prototype | **1,705 lines**, **239 `st.*` calls**, **2 top-level functions** | `app.py` |
| Total tracked Python + JSX + JS | **12,208 lines** | `git ls-files '*.py' '*.jsx' '*.js'`, excl. `package-lock.json` |
| RMP ranking formula | `rating*20 + min(reviews,50) − difficulty*2` | `professor_ranking.py:281` |
| Prompt truncation limits | 20 → 15 available, 8 completed, 8 requirements | `api/main.py:185`; `llm_integration.py:264,272,284` |

**Cache hit behavior — stated precisely, because the naive version is wrong.**
The RMP cache is a disk-backed dict at `data/rmp_cache.json`, keyed
`"{school_id}|{lowercased name}"`, with **no TTL and no invalidation**
(`rmp_integration.py:50-76`). Successful lookups are cached permanently; **misses and errors are
never cached** (lines 154-156, 189-191), so unknown professors re-hit the network every time.
The file is gitignored and Render's filesystem is ephemeral, so the cache starts empty on every
deploy. **There is no measured hit rate anywhere in this repo** — `cache_stats()`
(`rmp_integration.py:78`) exists but is never called, and nothing logs hits or misses. Any
specific hit-rate percentage would be invented; do not quote one.

**Do not quote** (no support in this repo): user counts, request volumes, latency numbers,
accuracy or parse-success rates, uptime, or "N students helped". None are measured or logged
anywhere in the codebase.

---

## 10. Unclear from code

- **Whether the Banner endpoints still work.** Both clients target live third-party systems with
  no recorded fixtures and no integration tests. `data/gsu_sections_real.json` (12 entries) and
  `data/gatech_sections_real.json` (31) are committed outputs from a past manual run
  (`gsu_banner_api.py:425-432` writes exactly this file from `__main__`), not a test harness.
  Whether the handshake succeeds today can only be determined by running it.
- **Whether the Georgia Tech RMP school ID is right.** `U2Nob29sLTM2MQ==` decodes to `School-361`,
  exactly one above GSU's `School-360` (`rmp_integration.py:31-32`). Adjacent IDs for two
  unrelated universities is suspicious, but nothing in the repo verifies it and there is no test.
- **Why `csc_prerequisites_catalog_38.json` is catalog 38 while `GSUPrerequisiteParser.CATALOG_ID`
  defaults to 42.** `main()` (line 341) explicitly passes `"38"`, so the committed data is from
  the older catalog; whether that is deliberate or a stale artifact is not recorded.
- **Whether `railway.json` is live.** It sits alongside `render.yaml` and `Procfile`; only Render
  is referenced by `frontend/vercel.json`. Probably a superseded deploy target, but the repo does
  not say.
- **What `data/major_requirements/major_requirements_2025_2026.json` feeds.**
  `utils/major_requirements_loader.py` (325 lines) reads it, but **nothing imports that loader** —
  grep for `major_requirements_loader` across all tracked `.py` returns only the file itself. Both
  the loader and the data file are orphaned; whether they are pre-work for an unshipped feature or
  simply abandoned is not recorded anywhere.

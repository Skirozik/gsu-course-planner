from fastapi import FastAPI, UploadFile, File, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
import time
import traceback
import json
from collections import defaultdict, deque

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.academic_eval_parser import parse_academic_eval, get_next_semester_recommendations
from utils.gatech_parser import parse_gatech_degreeworks
from utils.llm_integration import CourseRecommender, APIKeyManager
from utils.catalog_loader import get_catalog_loader
from utils.prerequisites import check_prerequisites_met, COURSE_DATABASE
from utils.export_utils import generate_pdf_schedule, generate_ics_calendar, generate_text_schedule
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="GSU Course Planner API")

# CORS locked to an allowlist. Override via the ALLOWED_ORIGINS env var
# (comma-separated) in the host dashboard; defaults cover prod + local dev.
_DEFAULT_ORIGINS = [
    "https://prereqpilot.dev",
    "https://www.prereqpilot.dev",
    "http://localhost:5173",  # Vite dev server
    "http://localhost:3000",
]
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", ",".join(_DEFAULT_ORIGINS)).split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

catalog_loader = get_catalog_loader()


# ---------------------------------------------------------------------------
# Lightweight in-memory rate limiter (per client IP, sliding window).
# Protects the endpoints that spend Anthropic credits. Tune via env vars.
# Note: this is a best-effort per-process brake, not a global limit -- with more
# than one instance the effective ceiling multiplies. The real guard against
# runaway spend is the limit set in the Anthropic Console.
# ---------------------------------------------------------------------------
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "20"))        # requests...
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # ...per this many seconds
_rate_hits: defaultdict = defaultdict(deque)

# Matches the limit advertised on the upload screen.
MAX_UPLOAD_BYTES = 10 * 1024 * 1024

# Anthropic call budgets. The SDK defaults to a 600s read timeout with 2 retries
# and it retries timeouts, so an unbounded call can hold a request for ~30 minutes.
ANTHROPIC_TIMEOUT = float(os.getenv("ANTHROPIC_TIMEOUT", "25"))
ANTHROPIC_MAX_RETRIES = int(os.getenv("ANTHROPIC_MAX_RETRIES", "1"))

# /api/sections fans out to RateMyProfessors once per instructor, each with its own
# timeout and throttle, so its worst case grows with the size of the teaching staff.
# This caps the whole handler; sections still rank fine with partial ratings.
SECTIONS_BUDGET_S = float(os.getenv("SECTIONS_BUDGET_S", "45"))


def rate_limit(request: Request):
    # Trust the proxy-forwarded client IP (Vercel/Render set X-Forwarded-For).
    forwarded = request.headers.get("x-forwarded-for")
    client_ip = (
        forwarded.split(",")[0].strip()
        if forwarded
        else (request.client.host if request.client else "unknown")
    )

    now = time.time()
    hits = _rate_hits[client_ip]
    while hits and hits[0] <= now - RATE_LIMIT_WINDOW:
        hits.popleft()

    # Drop the key once its window empties. Pruning timestamps inside a deque never
    # removed the deque itself, so the map grew without bound for the lifetime of
    # the process -- one entry per distinct client IP ever seen.
    if not hits:
        del _rate_hits[client_ip]

    if len(hits) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait a moment and try again.",
        )
    hits.append(now)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log full detail server-side, but don't leak internals to the client.
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    context: Optional[dict] = None


class PreferencesRequest(BaseModel):
    eval_data: dict
    school: str
    career_goals: Optional[str] = ""
    max_courses: int = 4
    has_job: bool = False
    major: Optional[str] = None


@app.get("/api/health")
def health():
    api_key = APIKeyManager.get_api_key()
    catalogs = getattr(catalog_loader, "catalogs", {}) or {}
    # Course counts prove the data files shipped with the deployment. If the
    # catalog directory is missing, /api/recommendations silently degrades to the
    # much smaller COURSE_DATABASE, which is otherwise invisible from outside.
    return {
        "status": "ok",
        "has_api_key": bool(api_key),
        "catalogs": len(catalogs),
        "courses": sum(len(c.get("courses", {})) for c in catalogs.values()),
    }


def normalize_eval_data(raw: dict) -> dict:
    """Flatten student_info to top level and strip raw_text before sending to frontend."""
    info = raw.get("student_info", {})
    return {
        "gpa": info.get("gpa"),
        "total_credits": info.get("credits_applied", 0),
        "credits_required": info.get("credits_required", 120),
        "major": info.get("major", ""),
        "student_name": info.get("student_name", ""),
        "college": info.get("college", ""),
        "degree": info.get("degree", ""),
        "catalog_year": info.get("catalog_year", ""),
        "completed_courses": raw.get("completed_courses", []),
        "in_progress_courses": raw.get("in_progress_courses", []),
        "required_courses": raw.get("required_courses", []),
        "requirements_summary": raw.get("requirements_summary", {}),
        # raw_text intentionally excluded — too large for frontend
    }


@app.post("/api/parse-transcript", dependencies=[Depends(rate_limit)])
async def parse_transcript(school: str, file: UploadFile = File(...)):
    # Browsers hand us whatever case the file was saved with; "AUDIT.PDF" is a PDF.
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="That PDF is larger than 10 MB. Re-export just the DegreeWorks audit page.",
        )

    try:
        if school == "Georgia Tech":
            raw = parse_gatech_degreeworks(content)
        else:
            raw = parse_academic_eval(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not read that PDF: {str(e)[:150]}")

    data = normalize_eval_data(raw)

    # The parsers never raise on unrecognized content — they return an empty
    # result. Without this check that empty result is reported as success and the
    # user reaches the preferences step with no transcript at all.
    if not data["completed_courses"] and not data["in_progress_courses"] and not data["major"]:
        raise HTTPException(
            status_code=422,
            detail=(
                "No courses or major found in that PDF. It needs to be the DegreeWorks "
                "audit itself (saved as a PDF, not a scan or screenshot) — a transcript "
                "or class schedule will not work."
            ),
        )

    return {"success": True, "data": data}


@app.post("/api/recommendations", dependencies=[Depends(rate_limit)])
def get_recommendations(req: PreferencesRequest):
    api_key = APIKeyManager.get_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="API key not configured")

    eval_data = req.eval_data
    completed_records = eval_data.get("completed_courses", []) or []
    in_progress_records = eval_data.get("in_progress_courses", []) or []

    # Two questions that were previously collapsed into one list:
    #   taken     - is there any record of this course? (so we do not re-recommend it)
    #   satisfied - does that record clear the prerequisite's minimum grade?
    # A D in CSC 2720 earns credit toward the degree, so the course is "taken", but
    # it does not satisfy a prerequisite requiring a C. An in-progress enrolment has
    # no grade yet and counts as satisfying, because the student will have finished
    # it before the semester being planned.
    taken = {(c.get("course_code") or "").upper().strip() for c in completed_records}
    in_progress_codes = [(c.get("course_code") or "").upper().strip() for c in in_progress_records]
    taken |= set(in_progress_codes)
    taken.discard("")
    grades = {
        (c.get("course_code") or "").upper().strip(): c.get("grade")
        for c in completed_records
    }

    # Get available courses from catalog
    available_courses = []
    major = req.major or eval_data.get("major", "")
    catalog = catalog_loader.get_catalog(req.school, major) if major else None

    if catalog:
        # courses is a dict: { "CSC 1301": { name, credits, prerequisites, ... } }
        # Checked against the catalog's own prerequisites, not COURSE_DATABASE:
        # only 30 of 64 GSU CS courses and none of the 18 Georgia Tech courses exist
        # in COURSE_DATABASE, and get_prerequisites returns [] for anything absent,
        # which made the filter pass every unknown course unconditionally.
        for code, info in catalog.get("courses", {}).items():
            if code in taken:
                continue
            eligibility = catalog_loader.check_prerequisites_with_grades(
                req.school, major, code, completed_records, in_progress_codes
            )
            if eligibility.get("can_take"):
                available_courses.append({
                    "course_code": code,
                    "course_name": info.get("name", code),
                    "credits": info.get("credits", 3),
                })
    else:
        for code, info in COURSE_DATABASE.items():
            if code in taken:
                continue
            if check_prerequisites_met(code, taken, grades).get("can_take"):
                available_courses.append({
                    "course_code": code,
                    "course_name": info.get("name", code),
                    "credits": info.get("credits", 3),
                })

    available_courses = available_courses[:20]

    preferences = {
        "career_goals": req.career_goals,
        "max_courses": req.max_courses,
        "has_job": req.has_job,
    }

    degree_requirements = eval_data.get("degree_requirements", {})
    student_data = {
        "gpa": eval_data.get("gpa"),
        "total_credits": eval_data.get("total_credits", 0),
        "credits_required": eval_data.get("credits_required", 120),
        "completed_courses": eval_data.get("completed_courses", []),
        # in_progress counts as taken for prereq checking
        "in_progress_courses": eval_data.get("in_progress_courses", []),
    }

    try:
        recommender = CourseRecommender(api_key=api_key)
        result = recommender.generate_schedule(
            student_data=student_data,
            preferences=preferences,
            available_courses=available_courses,
            degree_requirements=degree_requirements,
        )
        return {
            "success": True,
            "recommendations": result,
            "available_courses": available_courses,
            # False means the catalog was missing and we silently served the much
            # smaller COURSE_DATABASE instead. Surfaced so it is diagnosable.
            "catalog_used": bool(catalog),
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat", dependencies=[Depends(rate_limit)])
def chat(req: ChatRequest):
    api_key = APIKeyManager.get_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="API key not configured")

    from anthropic import Anthropic
    client = Anthropic(
        api_key=api_key,
        timeout=ANTHROPIC_TIMEOUT,
        max_retries=ANTHROPIC_MAX_RETRIES,
    )

    ctx = req.context or {}
    recs = ctx.get("recommended_courses", [])
    rec_list = "\n".join(f"- {c.get('course_code')} {c.get('course_name','')}" for c in recs) or "None"

    system = f"""You are a friendly academic advisor AI for a college student. Be concise (2-4 sentences max unless they ask for detail), conversational, and encouraging.

Student profile:
- GPA: {ctx.get('gpa', 'N/A')}
- Credits completed: {ctx.get('total_credits', '?')}/{ctx.get('credits_required', 120)}
- Major: {ctx.get('major', 'Unknown')}

Recommended courses for next semester:
{rec_list}

Overall plan reasoning: {ctx.get('reasoning', '')}

Answer questions about their course plan, specific course choices, prerequisites, or academic strategy. Keep it short and helpful."""

    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        system=system,
        messages=messages,
    )
    reply = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
    return {"reply": reply}


class ExportRequest(BaseModel):
    courses: List[dict] = []
    student_info: Optional[dict] = None
    format: str = "pdf"


@app.post("/api/export", dependencies=[Depends(rate_limit)])
def export_plan(req: ExportRequest):
    courses = req.courses or []
    info = req.student_info or {}
    fmt = (req.format or "pdf").lower()

    if not courses:
        raise HTTPException(status_code=400, detail="No courses to export")

    try:
        if fmt == "pdf":
            buffer = generate_pdf_schedule(courses, info)
            return Response(
                content=buffer.getvalue(),
                media_type="application/pdf",
                headers={"Content-Disposition": 'attachment; filename="course-plan.pdf"'},
            )
        if fmt == "ics":
            ics = generate_ics_calendar(courses)
            return Response(
                content=ics,
                media_type="text/calendar",
                headers={"Content-Disposition": 'attachment; filename="course-plan.ics"'},
            )
        if fmt == "txt":
            text = generate_text_schedule(courses, info)
            return Response(
                content=text,
                media_type="text/plain",
                headers={"Content-Disposition": 'attachment; filename="course-plan.txt"'},
            )
        raise HTTPException(status_code=400, detail=f"Unknown export format: {fmt}")
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)[:100]}")


@app.get("/api/sections", dependencies=[Depends(rate_limit)])
def get_sections(course: str, school: str = "Georgia State University"):
    """Live course sections for a course, ranked by professor quality (RMP)."""
    from utils.gsu_banner_api import get_gsu_sections
    from utils.gatech_banner_api import get_gatech_sections
    from utils.section_recommender import get_ranked_sections

    course = (course or "").strip()
    if not course:
        raise HTTPException(status_code=400, detail="Missing course code")

    try:
        if "tech" in school.lower():
            raw_sections = get_gatech_sections(course)
        else:
            raw_sections = get_gsu_sections(course)
    except Exception:
        traceback.print_exc()
        raise HTTPException(status_code=502, detail="Could not reach the registration system")

    if not raw_sections:
        return {"course": course, "sections": []}

    ranked = get_ranked_sections(
        course,
        raw_sections,
        school=school,
        deadline=time.monotonic() + SECTIONS_BUDGET_S,
    )
    sections = [
        {
            "section": s.section,
            "crn": s.crn,
            "instructor": s.instructor_normalized,
            "time": s.time,
            "location": s.location,
            "rating": s.rating,
            "difficulty": s.difficulty,
            "num_reviews": s.num_reviews,
            "rmp_url": s.rmp_url,
            "rank": s.rank,
        }
        for s in ranked
    ]
    return {"course": course, "sections": sections}


class PlanFeedbackRequest(BaseModel):
    courses: List[dict] = []
    student: Optional[dict] = None
    school: str = ""


@app.post("/api/plan-feedback", dependencies=[Depends(rate_limit)])
def plan_feedback(req: PlanFeedbackRequest):
    api_key = APIKeyManager.get_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="API key not configured")
    if not req.courses:
        raise HTTPException(status_code=400, detail="No courses selected")

    from anthropic import Anthropic
    client = Anthropic(
        api_key=api_key,
        timeout=ANTHROPIC_TIMEOUT,
        max_retries=ANTHROPIC_MAX_RETRIES,
    )

    def _credits(c):
        try:
            return int(float(c.get("credits", 3) or 3))
        except (TypeError, ValueError):
            return 3

    course_lines = "\n".join(
        f"- {c.get('course_code', '?')} {c.get('course_name', '')} ({_credits(c)} cr)"
        for c in req.courses
    )
    total_credits = sum(_credits(c) for c in req.courses)
    s = req.student or {}

    system = (
        "You are a candid, experienced academic advisor giving a student honest, specific "
        "feedback on the schedule they have chosen. No preamble, no filler, no bullet lists — "
        "just a few plain sentences spoken directly to the student."
    )
    user = f"""A {req.school or 'university'} student finalized this course selection for next semester:
{course_lines}

That is {len(req.courses)} courses and {total_credits} credits.

Student profile:
- GPA: {s.get('gpa', 'N/A')}
- Credits completed: {s.get('total_credits', '?')} of {s.get('credits_required', 120)} toward a {s.get('major', 'their')} degree

In 3 to 5 sentences, assess THIS selection: is the workload and difficulty realistic for this
student, does it make solid progress toward the degree, and are there any sequencing or balance
concerns? End with one concrete suggestion only if it genuinely helps."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    feedback = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
    return {"feedback": feedback}

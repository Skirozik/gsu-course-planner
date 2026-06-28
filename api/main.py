from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
import traceback
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.academic_eval_parser import parse_academic_eval, get_next_semester_recommendations
from utils.gatech_parser import parse_gatech_degreeworks
from utils.llm_integration import CourseRecommender, APIKeyManager
from utils.catalog_loader import get_catalog_loader
from utils.prerequisites import check_prerequisites_met, COURSE_DATABASE
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="GSU Course Planner API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

catalog_loader = get_catalog_loader()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    traceback.print_exc()
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {str(exc)}"})


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
    return {"status": "ok", "has_api_key": bool(api_key)}


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


@app.post("/api/parse-transcript")
async def parse_transcript(school: str, file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()

    try:
        if school == "Georgia Tech":
            raw = parse_gatech_degreeworks(content)
        else:
            raw = parse_academic_eval(content)
        return {"success": True, "data": normalize_eval_data(raw)}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse transcript: {str(e)}")


@app.post("/api/recommendations")
def get_recommendations(req: PreferencesRequest):
    api_key = APIKeyManager.get_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="API key not configured")

    eval_data = req.eval_data
    completed = [c.get("course_code", "") for c in eval_data.get("completed_courses", [])]
    completed += [c.get("course_code", "") for c in eval_data.get("in_progress_courses", [])]

    # Get available courses from catalog
    available_courses = []
    major = req.major or eval_data.get("major", "")
    catalog = catalog_loader.get_catalog(req.school, major) if major else None

    if catalog:
        # courses is a dict: { "CSC 1301": { name, credits, prerequisites, ... } }
        for code, info in catalog.get("courses", {}).items():
            if code not in completed and check_prerequisites_met(code, set(completed)).get("can_take"):
                available_courses.append({
                    "course_code": code,
                    "course_name": info.get("name", code),
                    "credits": info.get("credits", 3),
                })
    else:
        for code, info in COURSE_DATABASE.items():
            if code not in completed and check_prerequisites_met(code, set(completed)).get("can_take"):
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
        return {"success": True, "recommendations": result, "available_courses": available_courses}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
def chat(req: ChatRequest):
    api_key = APIKeyManager.get_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="API key not configured")

    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)

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

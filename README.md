# PrereqPilot

**Upload your DegreeWorks PDF, get a prerequisite-aware course schedule for next semester — with live section times and professor ratings.**

### ▶ [prereqpilot.dev](https://prereqpilot.dev)

Built for Georgia State University and Georgia Tech students. React + FastAPI, deployed on Vercel + Render.

---

## Try it in 60 seconds

No account, no signup, and no transcript of your own required — three sanitized sample
transcripts for a fictional student are checked into this repo.

**1. Download a sample transcript** (right-click → Save link as)

| Sample | School | Profile |
|---|---|---|
| [sample-gsu-cs-mixed-grades.pdf](https://github.com/Skirozik/multischool-course-planner/raw/main/samples/sample-gsu-cs-mixed-grades.pdf) | Georgia State | CS major, 90/120 credits, mixed record with retakes and failed courses |
| [sample-gsu-cs-strong-grades.pdf](https://github.com/Skirozik/multischool-course-planner/raw/main/samples/sample-gsu-cs-strong-grades.pdf) | Georgia State | Same student, all A/B grades — a clean-record comparison |
| [sample-gatech-cs-junior.pdf](https://github.com/Skirozik/multischool-course-planner/raw/main/samples/sample-gatech-cs-junior.pdf) | Georgia Tech | CS junior, 89/126 credits, includes transfer credit |

**2. Open [prereqpilot.dev](https://prereqpilot.dev)**, pick the matching school, and drop the PDF on the upload box.

**3. Set preferences and hit generate.** You'll get a recommended course load, and expanding any
course fetches its live sections from the school's registration system, ranked by professor rating.

> **First load may take up to a minute.** The backend runs on Render's free tier
> (`plan: free` in [render.yaml](render.yaml)), which sleeps after idle — the first request wakes
> it. Everything after that is fast.

All three samples are verified end to end against the live site. See
[Sample verification](#sample-verification) for the measured results.

---

## What it does

- **Parses DegreeWorks PDFs** — pulls completed, in-progress, and still-needed courses plus GPA
  and credit progress out of the PDF text, with separate parsers for GSU and Georgia Tech formats.
- **Checks prerequisites** — filters the catalog down to courses whose prerequisites the student
  has already satisfied, so the recommendation step only ever sees eligible courses.
- **Generates a schedule** — Claude picks a balanced load from the eligible set, given the
  student's stated course count, career goals, and whether they're working.
- **Finds live sections** — queries each school's Ellucian Banner registration API directly for
  real CRNs, meeting times, and rooms.
- **Ranks by professor** — looks each instructor up on Rate My Professors and orders sections by
  rating, difficulty, and review count. Advisory only; nothing is hidden or blocked.
- **Exports** — the finished plan downloads as PDF, `.ics` calendar, or plain text.

---

## Architecture

```
Browser ──▶ prereqpilot.dev  (Vercel — React 19 + Vite SPA)
                 │  vercel.json rewrites /api/* to the backend, so the
                 │  browser only ever talks to one origin
                 ▼
           FastAPI + Uvicorn  (Render — 7 endpoints in api/main.py)
                 │
                 ├──▶ Anthropic Claude       schedule generation, plan feedback, advisor chat
                 ├──▶ Banner APIs            live sections (GSU GoSOLAR, GT OSCAR)
                 └──▶ Rate My Professors     professor ratings (GraphQL)
                 │
                 ▼
           utils/ — PDF parsers, prerequisite engine, catalog loader,
                    professor ranking, exporters
```

| Layer | Stack |
|---|---|
| Frontend | React 19, Vite 8, Tailwind CSS 3, axios — [`frontend/`](frontend/) |
| Backend | FastAPI, Uvicorn — [`api/main.py`](api/main.py) |
| PDF parsing | pdfplumber, with PyPDF2 as fallback — [`utils/academic_eval_parser.py`](utils/academic_eval_parser.py) |
| AI | Anthropic Claude (`claude-sonnet-4-6`, `claude-haiku-4-5` fallback) — [`utils/llm_integration.py`](utils/llm_integration.py) |
| Integrations | Ellucian Banner, Rate My Professors GraphQL — [`utils/`](utils/) |
| Hosting | Vercel (frontend), Render (backend) |

The backend exposes **7 endpoints** ([`api/main.py`](api/main.py)): transcript parsing,
recommendations, sections, chat, plan feedback, export, and health. Credit-spending endpoints sit
behind a per-IP sliding-window rate limiter, and CORS is restricted to an allowlist.

**Legacy:** [`app.py`](app.py) is the original Streamlit prototype this project started as. It is
kept for reference only — nothing in `api/` imports it, and it is not part of the deployed app.
The React + FastAPI stack above is the current application.

For a detailed, source-cited walkthrough of how it actually works — including the prerequisite
engine's internals and its known limitations — see
[CODEBASE_BREAKDOWN.md](CODEBASE_BREAKDOWN.md).

---

## Sample verification

Each sample was uploaded to the live site and taken through the full flow. Measured
2026-08-01 against `https://prereqpilot.dev`:

| Sample | Parse | Prerequisite filter | Schedule generated |
|---|---|---|---|
| `sample-gsu-cs-mixed-grades.pdf` | ✅ 25 completed, 4 in progress, 7 requirements | ✅ 20 eligible courses | ✅ 4 courses |
| `sample-gsu-cs-strong-grades.pdf` | ✅ 27 completed, 4 in progress, 7 requirements | ✅ 20 eligible courses | ✅ 4 courses |
| `sample-gatech-cs-junior.pdf` | ✅ 25 completed, 5 in progress, 8 requirements | ✅ 14 eligible courses | ✅ 4 courses |

No errors on any of the three. Every recommended course came from the eligible-course list — no
fabricated course codes in any run.

The sample PDFs are synthetic: student name `Student, Sample`, ID `000000000`, address and
advisor fields redacted in both the text layer and the document metadata. No real student data
is in this repository.

---

## Running it locally

Requires Python 3.11 (the version pinned in [`.devcontainer/devcontainer.json`](.devcontainer/devcontainer.json)) and Node with npm.

**Backend**

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # then add your key:
# ANTHROPIC_API_KEY=sk-ant-...

uvicorn api.main:app --reload     # http://localhost:8000
```

Get a Claude API key at <https://console.anthropic.com/>. Without one, transcript parsing and
live sections still work; the AI endpoints return 503.

**Frontend**

```bash
cd frontend
npm install
npm run dev                       # http://localhost:3000
```

The Vite dev server proxies `/api/*` to `http://localhost:8000`
([`frontend/vite.config.js`](frontend/vite.config.js)); override with `VITE_API_URL`.

**Tests**

```bash
pytest tests/                     # 12 tests
```

Covering the prerequisite resolver and the section-ranking logic. Test coverage is partial —
[CODEBASE_BREAKDOWN.md](CODEBASE_BREAKDOWN.md) has an honest per-module breakdown of what is and
isn't tested.

---

## Deployment

- **Backend → Render**, via the [`render.yaml`](render.yaml) blueprint. `ANTHROPIC_API_KEY` is set
  in the dashboard, never in git.
- **Frontend → Vercel**, root directory `frontend`, Vite preset.
  [`frontend/vercel.json`](frontend/vercel.json) rewrites `/api/*` to the backend so requests stay
  same-origin.

---

## Disclaimers

- **Not official.** Not affiliated with, endorsed by, or connected to Georgia State University or
  Georgia Tech.
- **Confirm with your advisor.** Recommendations are AI-generated and the prerequisite data is
  assembled from public catalogs; both can be wrong or out of date. This is a planning aid, not
  an authoritative degree audit.
- **Course availability is not guaranteed.** Section data is live at time of request; seats change.
- **Privacy.** Uploaded transcripts are parsed in-request and are not stored on disk or in a
  database.

---

## License

Educational project. Not affiliated with Georgia State University or Georgia Tech.

Built by [@Skirozik](https://github.com/Skirozik).

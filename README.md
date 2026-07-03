# 🎓 PrereqPilot

**Live at [prereqpilot.dev](https://prereqpilot.dev)**

An AI-powered course planning assistant for **Georgia State University** and **Georgia Tech** students. Upload your DegreeWorks evaluation and get a prerequisite-aware, AI-generated course schedule with live Rate My Professors ratings for each section.

## ✨ Features

- 📄 **DegreeWorks parsing** — extracts completed/in-progress/required courses, GPA, and credit progress from GSU and Georgia Tech evaluations
- 🎯 **AI recommendations** — Claude analyzes your transcript, remaining requirements, and preferences to recommend a balanced next semester
- 🔗 **Prerequisite engine** — resolves free-text prerequisite logic (AND/OR, minimum grades) into eligibility checks
- ⭐ **Rate My Professors integration** — ranks each course's live sections by professor quality
- 📡 **Live section data** — pulls real-time sections directly from each school's Banner registration API
- 🏫 **Multi-school** — Georgia State and Georgia Tech, with per-school parsers, catalogs, and APIs

## 🧱 Tech stack

| Layer | Stack |
|---|---|
| **Frontend** | React 19 + Vite + Tailwind CSS (`frontend/`) — deployed on **Vercel** |
| **Backend** | FastAPI + Uvicorn (`api/main.py`) — deployed on **Render** |
| **AI** | Anthropic Claude (`claude-sonnet-4-6`, `claude-haiku-4-5` fallback) |
| **Integrations** | Ellucian Banner APIs (live sections), Rate My Professors GraphQL |
| **Parsing** | pdfplumber / PyPDF2 (DegreeWorks), regex prerequisite resolver |

## 🏗️ Architecture

```
Browser ──▶ prereqpilot.dev (Vercel, React SPA)
                 │  /api/* rewrites (same-origin proxy, no CORS)
                 ▼
        FastAPI backend (Render) ──▶ Claude · Banner · Rate My Professors
                 │
                 ▼
        Shared Python logic (utils/): parsers, prerequisite engine,
        catalog loader, professor ranking, exports
```

## 🚀 Local development

### 1. Backend (FastAPI)

```bash
# from the repo root
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # then add your key:
# ANTHROPIC_API_KEY=sk-ant-...

uvicorn api.main:app --reload     # serves http://localhost:8000
```

Get a Claude API key at <https://console.anthropic.com/>.

### 2. Frontend (React)

```bash
cd frontend
npm install
npm run dev                       # serves http://localhost:5173
```

The dev server proxies `/api/*` to the backend. For production, `frontend/vercel.json`
rewrites `/api/*` to the deployed backend URL.

> **Legacy:** the original Streamlit prototype still lives in `app.py`
> (`streamlit run app.py`). The React + FastAPI stack above is the current app.

## 📖 How to use

1. **Select your school** (Georgia State or Georgia Tech)
2. **Upload your DegreeWorks PDF** (GSU: PAWS → DegreeWorks; GT: OSCAR → DegreeWorks)
3. **Set preferences** — major, career goals, course load, difficulty
4. **Generate** — get AI recommendations with RMP-ranked sections and exports

## ☁️ Deployment

- **Backend → Render:** `render.yaml` blueprint (start: `uvicorn api.main:app`). Set `ANTHROPIC_API_KEY` as a secret in the dashboard.
- **Frontend → Vercel:** root directory `frontend`, Vite preset. `frontend/vercel.json` proxies `/api/*` to the Render backend (same-origin, so no CORS).
- **CORS** is locked to the production domain via the `ALLOWED_ORIGINS` env var, and the credit-spending API endpoints are rate-limited.

## ⚠️ Disclaimers

- **Not official** — not affiliated with Georgia State University or Georgia Tech
- **Verify everything** — always confirm course plans with your academic advisor
- **Privacy** — transcript data is processed for the request and not permanently stored
- **Accuracy** — recommendations are AI-generated and may contain errors; course availability is not guaranteed

## 📝 License

For educational purposes. Not affiliated with Georgia State University or Georgia Tech.

---

Built by [@Skirozik](https://github.com/Skirozik) for GSU and Georgia Tech students.

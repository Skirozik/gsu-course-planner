# Retired prototype

`streamlit_app.py` was the original single-file Streamlit version of PrereqPilot.
It is superseded by the FastAPI backend in `api/` plus the React frontend in
`frontend/`, and nothing imports it. Kept for reference only.

It behaves differently from the deployed app in several places, so do not treat it
as documentation of current behavior.

    pip install -r legacy/requirements-streamlit.txt
    streamlit run legacy/streamlit_app.py

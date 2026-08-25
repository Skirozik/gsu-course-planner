"""Vercel entrypoint.

Vercel's Python runtime looks for a top-level ``app`` at a small set of known
filenames. The real application lives in ``api/main.py``; this file exists so the
entrypoint is unambiguous rather than depending on whether ``api/`` is treated as
an entrypoint directory — Vercel's own FastAPI reference and its KB guide
disagree on that point.

It also keeps the probe off ``app.py``, which is the first name Vercel looks for
and which used to hold the Streamlit prototype (no top-level ``app`` symbol, so
the build would have failed). That file now lives in ``legacy/``.
"""

from api.main import app  # noqa: F401

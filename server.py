"""Default ASGI entry point — re-exports the FastAPI app for external servers.

Importable anywhere::

    uvicorn server:app                    # run locally
    gunicorn -k uvicorn.workers.UvicornWorker "server:app"
    # and any tool that looks for `server.py` / `app` (e.g. enlace).

This file is intentionally tiny: it inserts the semix repo root onto
``sys.path`` so the sibling ``webapp/`` package can be imported regardless
of the current working directory, then re-exports the FastAPI app.
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from webapp.api.main import app  # noqa: E402,F401  (public re-export)

__all__ = ["app"]

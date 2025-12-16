"""Vercel Python entrypoint for FastAPI."""

from pathlib import Path
import sys

# Ensure project root is importable when executed from the api/ directory.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skillslike.api.main import app  # noqa: E402

# Expose as module-level variable for Vercel.
__all__ = ["app"]

import os

# Disable GitPython auto-refresh executable check in serverless environments (Vercel)
os.environ["GIT_PYTHON_REFRESH"] = "0"
os.environ["GIT_PYTHON_GIT_EXECUTABLE"] = "git"

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.main import app

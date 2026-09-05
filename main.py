"""Root entrypoint for SHIVANG PLAGCHECK AI Backend.

Enables simple start commands such as:
`uvicorn main:app --host 0.0.0.0 --port $PORT`
"""

import sys
from pathlib import Path

# Add backend directory to sys.path so that `app.*` imports resolve seamlessly
backend_dir = Path(__file__).resolve().parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""Entry point. Run with:
    uvicorn src.server:app --host 0.0.0.0 --port 8000
"""

import uvicorn

from src.app import app

if __name__ == "__main__":
    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=True)

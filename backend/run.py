"""Script to run the FastAPI backend"""
import uvicorn
from pathlib import Path

if __name__ == "__main__":
    # Get backend directory
    backend_dir = Path(__file__).parent
    
    # Watch all Python files in backend directory and subdirectories
    reload_dirs = [str(backend_dir)]
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=reload_dirs,
        reload_includes=["*.py"],
        reload_excludes=["*.pyc", "__pycache__", "*.db", "*.json"],
        reload_delay=0.25  # Add small delay to avoid rapid reloads
    )


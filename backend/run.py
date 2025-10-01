# run.py
import uvicorn
import sys
import os

if __name__ == "__main__":
    # Add the project root to the path to allow the 'app' package to be found.
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)

    # Point uvicorn to the app object within the 'main' module inside the 'app' package.
    # The reload_dirs argument ensures the reloader watches the correct directory.
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=["app"])
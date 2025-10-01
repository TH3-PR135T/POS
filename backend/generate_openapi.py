# backend/scripts/generate_openapi.py
import json
import os
import sys

# Add the project root to the Python path to allow imports from the 'backend' module
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from main import app

def generate_openapi_spec():
    """
    Generates the OpenAPI JSON specification and saves it to the project root.
    """
    output_path = os.path.join(project_root, 'openapi.json')
    
    with open(output_path, 'w') as f:
        json.dump(app.openapi(), f, indent=2)
        
    print(f"✅ OpenAPI specification successfully generated at: {output_path}")

if __name__ == "__main__":
    generate_openapi_spec()
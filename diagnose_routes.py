from fastapi import FastAPI
from fastapi.testclient import TestClient
import sys
import os
import json

# Add app directory to sys.path
sys.path.append(os.path.join(os.getcwd(), "BACKEND/app"))

try:
    from main import app
except ImportError as e:
    print(f"Error importing app: {e}")
    sys.exit(1)

def print_routes(app: FastAPI):
    print("\n=== ROUTE DIAGNOSTIC ===")
    print(f"{'PATH':<50} {'NAME':<50} {'METHODS'}")
    print("-" * 120)
    
    # Collect routes
    routes = []
    for route in app.routes:
        methods = getattr(route, "methods", None) or ["ALL"]
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": methods
        })
    
    # Sort for readability, or keep order for precedence check
    # We keep order to check precedence
    for r in routes:
        if "admin" in r["path"]:
            print(f"{r['path']:<50} {r['name']:<50} {r['methods']}")
            
    print("-" * 120)

def test_template_route():
    print("\n=== TESTING /admin/newsletter/templates ===")
    client = TestClient(app)
    
    try:
        response = client.get("/admin/newsletter/templates")
        print(f"Status Code: {response.status_code}")
        
        content = response.text
        print(f"Content Length: {len(content)}")
        print("First 200 chars:")
        print(content[:200])
        
        if "{% extends" in content:
            print("\n❌ FAILURE: Raw Jinja tags detected!")
            print("The route is returning the raw file content instead of rendering it.")
        elif "<!DOCTYPE html>" in content and "Template Library" in content:
            print("\n✅ SUCCESS: Rendered HTML detected!")
        else:
            print("\n⚠️ UNKNOWN: Content doesn't match expected success or failure patterns.")
            
    except Exception as e:
        print(f"❌ Exception during test request: {e}")

if __name__ == "__main__":
    print_routes(app)
    test_template_route()

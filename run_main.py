#!/usr/bin/env python
"""Startup script for the main application"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the app
from backend.main import app
from waitress import serve

if __name__ == "__main__":
    print("Starting BdeB-Go main application...")
    print(f"Serving on http://127.0.0.1:5000")
    serve(app, host="127.0.0.1", port=5000, threads=8)
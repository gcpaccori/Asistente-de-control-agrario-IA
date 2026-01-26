"""
Vercel serverless function entry point for Flask app.
This file wraps the Flask application to work as a Vercel serverless function.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import app, init_db, migrate_db, ensure_agent_defaults

# Initialize database on cold start
try:
    init_db()
    migrate_db()
    with app.app_context():
        ensure_agent_defaults()
except Exception as e:
    print(f"Warning: Database initialization failed: {e}")
    # Continue anyway as some routes might still work

# Vercel expects a handler function or WSGI app
# The app object itself is the WSGI application
handler = app

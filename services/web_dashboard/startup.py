#!/usr/bin/env python3
"""
Startup script for Hospital Web Dashboard
Handles database initialization and starts the Flask app
"""

import os
import sys
import subprocess

def main():
    print("🚀 Starting Hospital Web Dashboard...")
    
    # Check if database exists and is not empty
    db_path = "/app/healthcare.db"
    
    if not os.path.exists(db_path) or os.path.getsize(db_path) == 0:
        print("🏥 Initializing database...")
        try:
            result = subprocess.run([sys.executable, "simple_db_init.py"], 
                                  capture_output=True, text=True, check=True)
            print("✅ Database initialized!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Database initialization failed: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            sys.exit(1)
        except FileNotFoundError:
            print("⚠️  simple_db_init.py not found, skipping database initialization")
    else:
        print("ℹ️  Database already exists")
    
    # Start the Flask application
    print("🌐 Starting Flask application...")
    try:
        # Import and run the Flask app
        from app import app
        app.run(host='0.0.0.0', port=5000, debug=False)
    except ImportError as e:
        print(f"❌ Failed to import Flask app: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start Flask app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
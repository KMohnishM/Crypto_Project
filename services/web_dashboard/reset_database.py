#!/usr/bin/env python3
"""
Database reset script for the Hospital Monitoring Dashboard
This will drop all tables and recreate them with fresh data.
"""

import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db

def reset_database():
    """Reset the database by dropping all tables and recreating them"""
    print("🔄 Resetting Hospital Monitoring Database...")
    
    with app.app_context():
        try:
            # Drop all tables
            print("🗑️  Dropping all tables...")
            db.drop_all()
            print("✅ All tables dropped successfully!")
            
            # Recreate all tables
            print("📋 Creating fresh database tables...")
            db.create_all()
            print("✅ Fresh database tables created successfully!")
            
            print("\n🎉 Database reset complete!")
            print("💡 Run 'python init_database.py' to populate with sample data.")
            
        except Exception as e:
            print(f"❌ Error during database reset: {e}")
            raise

if __name__ == '__main__':
    confirm = input("⚠️  This will delete ALL data. Are you sure? (yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        reset_database()
    else:
        print("❌ Database reset cancelled.")

#!/usr/bin/env python3
"""
Simple database initialization script that always works
"""
import os
import sqlite3
from datetime import datetime

def create_simple_database():
    """Create database and tables using raw SQL"""
    
    # Define the database path
    db_path = 'healthcare.db'
    
    print("🏥 Creating Hospital Database...")
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Removed existing database")
    
    # Create new database connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(256) NOT NULL,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                role VARCHAR(20) NOT NULL,
                department VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Create patients table
        cursor.execute('''
            CREATE TABLE patients (
                patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                mrn VARCHAR(20) UNIQUE NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                date_of_birth DATE NOT NULL,
                gender VARCHAR(10) NOT NULL,
                blood_type VARCHAR(3),
                address VARCHAR(255),
                phone VARCHAR(20),
                email VARCHAR(100),
                emergency_contact VARCHAR(100),
                emergency_phone VARCHAR(20),
                admission_date DATETIME,
                discharge_date DATETIME,
                status VARCHAR(20) NOT NULL,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create patient_locations table
        cursor.execute('''
            CREATE TABLE patient_locations (
                location_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                hospital VARCHAR(50) NOT NULL,
                department VARCHAR(50) NOT NULL,
                ward VARCHAR(50) NOT NULL,
                bed VARCHAR(20),
                assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id)
            )
        ''')
        
        # Create user_sessions table
        cursor.execute('''
            CREATE TABLE user_sessions (
                session_id VARCHAR(128) PRIMARY KEY,
                user_id INTEGER NOT NULL,
                ip_address VARCHAR(45),
                user_agent VARCHAR(256),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        print("✅ Database tables created successfully!")
        
        # Insert default admin user (password hash for 'admin')
        from werkzeug.security import generate_password_hash
        admin_password_hash = generate_password_hash('admin')
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', 'admin@hospital.com', admin_password_hash, 'System', 'Administrator', 'admin', 1))
        
        print("👤 Created admin user: username=admin, password=admin")
        
        # Commit changes
        conn.commit()
        print("💾 Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_simple_database()
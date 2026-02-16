#!/usr/bin/env python3
"""
Simple database initialization script that always works
Supports both plain SQLite and SQLCipher encrypted databases
"""
import os
import sys
from datetime import datetime

def create_simple_database():
    """Create database and tables using raw SQL"""
    
    # Define the database path - must match Flask app configuration
    # Flask uses: DATABASE_URL=sqlite:///instance/healthcare.db
    db_dir = 'instance'
    db_path = os.path.join(db_dir, 'healthcare.db')
    
    # Create instance directory if it doesn't exist
    os.makedirs(db_dir, exist_ok=True)
    
    print("🏥 Creating Hospital Database...")
    print(f"📁 Database location: {db_path}")
    
    # Check if encryption is enabled
    ENABLE_DB_ENCRYPTION = os.getenv('ENABLE_DB_ENCRYPTION', 'false').lower() == 'true'
    DB_ENCRYPTION_KEY = os.getenv('DB_ENCRYPTION_KEY', 'dev-db-key-change-in-production')
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Removed existing database")
    
    # Try to use SQLCipher if encryption is enabled
    if ENABLE_DB_ENCRYPTION:
        try:
            from pysqlcipher3 import dbapi2 as sqlcipher
            conn = sqlcipher.connect(db_path)
            cursor = conn.cursor()
            # Set encryption key
            cursor.execute(f"PRAGMA key = '{DB_ENCRYPTION_KEY}'")
            cursor.execute("PRAGMA cipher_page_size = 4096")
            print("🔐 Using SQLCipher encryption")
        except ImportError:
            print("⚠️  SQLCipher not available, falling back to plain SQLite")
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
    else:
        # Use plain SQLite
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("📝 Using plain SQLite (encryption disabled)")
    
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
                requested_role VARCHAR(20),
                department VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
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
        
        # Optionally insert a default admin user. Set CREATE_DEFAULT_ADMIN=false to skip.
        from werkzeug.security import generate_password_hash
        CREATE_DEFAULT_ADMIN = os.getenv('CREATE_DEFAULT_ADMIN', 'true').lower() == 'true'
        if CREATE_DEFAULT_ADMIN:
            admin_password_hash = generate_password_hash('admin')
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('admin', 'admin@hospital.com', admin_password_hash, 'System', 'Administrator', 'admin', 1))
            print("👤 Created admin user: username=admin, password=admin")
        else:
            print("ℹ️  Skipping creation of default admin (CREATE_DEFAULT_ADMIN=false)")
        
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
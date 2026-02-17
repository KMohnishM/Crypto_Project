"""
Database configuration with encryption support
Uses SQLCipher for encrypted SQLite database
"""
import os
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

# Create a single SQLAlchemy instance
db = SQLAlchemy()

def init_encrypted_db(app):
    """
    Initialize database with encryption support
    
    For SQLCipher, the PRAGMA key must be set immediately after connection.
    This is handled via SQLAlchemy events.
    """
    DB_ENCRYPTION_KEY = os.getenv('DB_ENCRYPTION_KEY', 'dev-db-key-change-in-production')
    
    # Check if encryption is enabled
    ENABLE_DB_ENCRYPTION = os.getenv('ENABLE_DB_ENCRYPTION', 'false').lower() == 'true'
    
    if ENABLE_DB_ENCRYPTION:
        try:
            # Import SQLCipher
            from pysqlcipher3 import dbapi2 as sqlcipher
            
            # Modify SQLAlchemy configuration to use pysqlcipher3
            app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                'module': sqlcipher,
                'poolclass': StaticPool,
                'connect_args': {'check_same_thread': False}
            }
            
            # Set up encryption key on each connection (global event listener)
            @event.listens_for(Engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                """Set encryption key for each new connection"""
                cursor = dbapi_conn.cursor()
                cursor.execute(f"PRAGMA key = '{DB_ENCRYPTION_KEY}'")
                cursor.execute("PRAGMA cipher_page_size = 4096")
                cursor.close()
            
            print("Database encryption ENABLED (SQLCipher)")
            
        except ImportError:
            print("WARNING: SQLCipher not available - using plain SQLite")
            print("   Install with: pip install pysqlcipher3")
    else:
        print("WARNING: Database encryption DISABLED (set ENABLE_DB_ENCRYPTION=true to enable)")
    
    # Initialize database
    db.init_app(app)
    
    return db

def get_db_info():
    """Get database configuration info"""
    return {
        'type': 'SQLCipher' if os.getenv('ENABLE_DB_ENCRYPTION', 'false').lower() == 'true' else 'SQLite',
        'encrypted': os.getenv('ENABLE_DB_ENCRYPTION', 'false').lower() == 'true',
        'path': os.getenv('DATABASE_URL', 'sqlite:///healthcare.db')
    }

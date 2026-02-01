"""
Database configuration and initialization
"""
from flask_sqlalchemy import SQLAlchemy

# Create a single SQLAlchemy instance that will be shared across all models
db = SQLAlchemy()

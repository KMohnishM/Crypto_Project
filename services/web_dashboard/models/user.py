from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize SQLAlchemy without app (we'll initialize it later in app.py)
db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)  # Changed from user_id to id for Flask-Login
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'doctor', 'nurse', 'technician'
    department = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_permission(self, permission):
        """
        Check if user has a specific permission based on role
        Permissions by role:
        - admin: All permissions
        - doctor: view_patients, edit_patients, view_vitals, add_vitals
        - nurse: view_patients, view_vitals, add_vitals
        - technician: view_patients, view_vitals
        """
        permissions = {
            'admin': ['all', 'view_patients', 'edit_patients', 'view_vitals', 'add_vitals', 'manage_users'],
            'doctor': ['view_patients', 'edit_patients', 'view_vitals', 'add_vitals'],
            'nurse': ['view_patients', 'view_vitals', 'add_vitals'],
            'technician': ['view_patients', 'view_vitals']
        }
        
        if self.role not in permissions:
            return False
            
        return permission in permissions[self.role] or 'all' in permissions[self.role]
    
    def __repr__(self):
        return f'<User {self.username}>'


class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    session_id = db.Column(db.String(128), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))
    
    def __repr__(self):
        return f'<UserSession {self.session_id}>'
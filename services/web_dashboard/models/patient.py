from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from models.user import db, User

class Patient(db.Model):
    __tablename__ = 'patients'
    
    patient_id = db.Column(db.Integer, primary_key=True)
    mrn = db.Column(db.String(20), unique=True, nullable=False)  # Medical Record Number
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(10), nullable=False)  # 'male', 'female', 'other'
    blood_type = db.Column(db.String(3))  # 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'
    address = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    admission_date = db.Column(db.DateTime)
    discharge_date = db.Column(db.DateTime)
    status = db.Column(db.String(20), nullable=False)  # 'admitted', 'discharged', 'critical', 'stable'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    locations = db.relationship('PatientLocation', backref='patient', lazy=True)
    vital_signs = db.relationship('PatientVitalSign', backref='patient', lazy=True)
    medical_history = db.relationship('PatientMedicalHistory', backref='patient', lazy=True)
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        today = datetime.today()
        birth_date = self.date_of_birth
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    
    def get_current_location(self):
        """Get the current active location of the patient"""
        location = PatientLocation.query.filter_by(patient_id=self.patient_id, active=True).first()
        if location:
            return {
                'hospital': location.hospital,
                'department': location.department,
                'ward': location.ward,
                'bed': location.bed
            }
        return None
    
    def get_recent_vitals(self, limit=1):
        """Get the most recent vital signs for the patient"""
        vitals = PatientVitalSign.query.filter_by(patient_id=self.patient_id)\
            .order_by(PatientVitalSign.recorded_at.desc())\
            .limit(limit).all()
        return vitals
    
    def to_dict(self):
        """Convert patient object to dictionary for API responses"""
        return {
            'patient_id': self.patient_id,
            'mrn': self.mrn,
            'name': self.get_full_name(),
            'age': self.get_age(),
            'gender': self.gender,
            'blood_type': self.blood_type,
            'status': self.status,
            'location': self.get_current_location(),
            'admission_date': self.admission_date.isoformat() if self.admission_date else None,
            'discharge_date': self.discharge_date.isoformat() if self.discharge_date else None
        }
    
    def __repr__(self):
        return f'<Patient {self.mrn}: {self.get_full_name()}>'


class PatientLocation(db.Model):
    __tablename__ = 'patient_locations'
    
    location_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    hospital = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(50), nullable=False)
    ward = db.Column(db.String(50), nullable=False)
    bed = db.Column(db.String(20))
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<PatientLocation {self.hospital}/{self.department}/{self.ward}>'


class PatientVitalSign(db.Model):
    __tablename__ = 'patient_vital_signs'
    
    vital_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    heart_rate = db.Column(db.Float)
    spo2 = db.Column(db.Float)
    bp_systolic = db.Column(db.Float)
    bp_diastolic = db.Column(db.Float)
    respiratory_rate = db.Column(db.Float)
    temperature = db.Column(db.Float)
    etco2 = db.Column(db.Float)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with user who recorded
    user = db.relationship('User', backref=db.backref('recorded_vitals', lazy=True))
    
    def to_dict(self):
        """Convert vital signs to dictionary for API responses"""
        return {
            'vital_id': self.vital_id,
            'patient_id': self.patient_id,
            'heart_rate': self.heart_rate,
            'spo2': self.spo2,
            'bp_systolic': self.bp_systolic,
            'bp_diastolic': self.bp_diastolic,
            'respiratory_rate': self.respiratory_rate,
            'temperature': self.temperature,
            'etco2': self.etco2,
            'recorded_by': self.user.get_full_name() if self.user else None,
            'recorded_at': self.recorded_at.isoformat()
        }
    
    def __repr__(self):
        return f'<PatientVitalSign for patient {self.patient_id} at {self.recorded_at}>'


class PatientMedicalHistory(db.Model):
    __tablename__ = 'patient_medical_history'
    
    history_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.patient_id'), nullable=False)
    condition = db.Column(db.String(100), nullable=False)
    diagnosis_date = db.Column(db.Date)
    treatment = db.Column(db.Text)
    medication = db.Column(db.String(255))
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with user who recorded
    user = db.relationship('User', backref=db.backref('recorded_history', lazy=True))
    
    def __repr__(self):
        return f'<PatientMedicalHistory {self.condition} for patient {self.patient_id}>'
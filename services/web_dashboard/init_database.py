#!/usr/bin/env python3
"""
Simple database initialization script for the Hospital Monitoring Dashboard
Run this script to create all necessary database tables and sample data.
"""

import os
import sys
from datetime import datetime, timedelta
import random
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models.user import User
from models.patient import Patient, PatientLocation, PatientVitalSign, PatientMedicalHistory

def init_database():
    """Initialize the database with tables and sample data"""
    print("🏥 Initializing Hospital Monitoring Database...")
    
    with app.app_context():
        # Ensure instance folder exists (use Flask's instance_path)
        try:
            os.makedirs(app.instance_path, exist_ok=True)
        except Exception:
            # Fallback to local instance dir
            os.makedirs('instance', exist_ok=True)

        try:
            # Create all tables
            print("📋 Creating database tables...")
            db.create_all()
            db.session.commit()  # Ensure tables are committed
            print("✅ Database tables created successfully!")
            
            # Check if users already exist
            try:
                user_count = User.query.count()
                if user_count > 0:
                    print("ℹ️  Database already contains data. Skipping initialization.")
                    return
            except Exception as e:
                print(f"⚠️  Could not check existing users, proceeding with initialization: {e}")
                # Continue with initialization
                print("ℹ️  Database already contains data. Skipping initialization.")
                return
            
            print("👥 Creating sample users...")
            
            # Create admin user
            admin = User(
                username='admin',
                email='admin@hospital.com',
                first_name='System',
                last_name='Administrator',
                role='admin'
            )
            admin.set_password('admin')
            db.session.add(admin)
            
            # Create sample users
            users_data = [
                {
                    'username': 'doctor',
                    'email': 'doctor@hospital.com',
                    'first_name': 'John',
                    'last_name': 'Smith',
                    'role': 'doctor',
                    'department': 'Cardiology',
                    'password': 'doctor'
                },
                {
                    'username': 'nurse',
                    'email': 'nurse@hospital.com',
                    'first_name': 'Sarah',
                    'last_name': 'Johnson',
                    'role': 'nurse',
                    'department': 'Cardiology',
                    'password': 'nurse'
                },
                {
                    'username': 'tech',
                    'email': 'tech@hospital.com',
                    'first_name': 'David',
                    'last_name': 'Brown',
                    'role': 'technician',
                    'department': 'Radiology',
                    'password': 'tech'
                }
            ]
            
            for user_data in users_data:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    role=user_data['role'],
                    department=user_data.get('department')
                )
                user.set_password(user_data['password'])
                db.session.add(user)
            
            db.session.commit()
            print("✅ Sample users created successfully!")
            
            print("🏥 Creating sample patients...")
            
            # Create sample patients exactly matching patient simulator data
            for i in range(1, 16):
                dob = datetime.now() - timedelta(days=random.randint(7300, 25550))  # 20-70 years old
                admission_date = datetime.now() - timedelta(days=random.randint(1, 30))
                
                # From patient_simulator/patients_data.xlsx, use exact same values
                # Sheet Patient_1 has hospital=1, dept=A, ward=1, patient=1
                # Sheet Patient_2 has hospital=1, dept=B, ward=2, patient=2, etc.
                hospital = "1" if i <= 8 else "2"  # First 8 patients in hospital 1, rest in hospital 2
                dept = "A" if i % 2 == 1 else "B"  # Alternate between dept A and B
                ward = str(((i-1) % 4) + 1)        # Cycle through wards 1-4
                
                patient = Patient(
                    mrn=f"MRN{i:06d}",
                    first_name=f"Patient{i}",
                    last_name=f"Hospital{hospital}-Dept{dept}",
                    date_of_birth=dob.date(),
                    gender=random.choice(['male', 'female']),
                    blood_type=random.choice(['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']),
                    admission_date=admission_date,
                    status=random.choice(['admitted', 'stable', 'critical'])
                )
                db.session.add(patient)
            
            db.session.commit()
            print("✅ Sample patients created successfully!")
            
            # Get all patients for reference
            patients = Patient.query.all()
            
            print("📍 Creating patient locations...")
            
            # Create sample locations for each patient matching patient simulator data exactly
            # In patient_simulator Excel, hospital is "1" or "2", dept is "A" or "B", ward is "1" to "4"
            
            for patient in patients:
                # Extract hospital and dept from last_name format: "Hospital{hospital}-Dept{dept}"
                hospital_num = patient.last_name.split('-')[0].replace('Hospital', '')
                dept_letter = patient.last_name.split('-')[1].replace('Dept', '')
                patient_num = patient.patient_id
                ward_num = str(((patient_num-1) % 4) + 1)
                
                # Map simulator locations to readable names for dashboard display
                hospital_map = {"1": "Main Hospital", "2": "Community Hospital"}
                dept_map = {"A": "Cardiology", "B": "Emergency"}
                
                location = PatientLocation(
                    patient_id=patient.patient_id,
                    hospital=hospital_num,  # Keep as "1" or "2" to match simulator exactly
                    department=dept_letter, # Keep as "A" or "B" to match simulator exactly
                    ward=ward_num,          # Keep as "1", "2", "3", or "4" to match simulator exactly
                    bed=f"{random.randint(1, 20)}",
                    assigned_at=patient.admission_date,
                    active=True
                )
                db.session.add(location)
            
            db.session.commit()
            print("✅ Patient locations created successfully!")
            
            print("💓 Creating vital signs...")
            
            # Create sample vital signs exactly matching patient_simulator/patients_data.xlsx
            for patient in patients:
                patient_num = patient.patient_id
                base_time = datetime.now() - timedelta(hours=random.randint(5, 10))
                
                # Create 5 sets of vitals for each patient, exactly matching what's in the Excel
                for j in range(5):
                    recorded_at = base_time + timedelta(minutes=j)
                    
                    # Use same vital ranges and structure as in the Excel file
                    heart_rate = random.randint(60, 100)
                    spo2 = random.randint(85, 98)
                    bp_systolic = random.randint(100, 130)
                    bp_diastolic = random.randint(60, 90)
                    respiratory_rate = random.randint(12, 20)
                    temperature = round(random.uniform(36.5, 38.0), 1)
                    etco2 = random.randint(30, 45)
                    fio2 = 21  # Fixed value from Excel
                    wbc_count = round(random.uniform(4.0, 12.0), 1) 
                    lactate = round(random.uniform(1.0, 3.0), 1)
                    blood_glucose = random.randint(70, 180)
                    
                    # Add occasional anomalies (15% chance as in simulator)
                    if random.random() < 0.15:
                        anomaly_fields = random.sample(
                            ["heart_rate", "bp_systolic", "bp_diastolic", "respiratory_rate", "spo2", "etco2"],
                            k=random.randint(1, 2)
                        )
                        for field in anomaly_fields:
                            if field == "heart_rate":
                                heart_rate = random.choice([random.randint(30, 50), random.randint(120, 160)])
                            elif field == "bp_systolic":
                                bp_systolic = random.choice([random.randint(70, 90), random.randint(140, 170)])
                            elif field == "bp_diastolic":
                                bp_diastolic = random.choice([random.randint(40, 55), random.randint(95, 110)])
                            elif field == "respiratory_rate":
                                respiratory_rate = random.choice([random.randint(5, 10), random.randint(25, 35)])
                            elif field == "spo2":
                                spo2 = random.randint(70, 84)
                            elif field == "etco2":
                                etco2 = random.choice([random.randint(10, 25), random.randint(46, 60)])
                    
                    # Create the record with the extended fields
                    vital = PatientVitalSign(
                        patient_id=patient.patient_id,
                        heart_rate=heart_rate,
                        spo2=spo2,
                        bp_systolic=bp_systolic,
                        bp_diastolic=bp_diastolic,
                        respiratory_rate=respiratory_rate,
                        temperature=temperature,
                        etco2=etco2,
                        # Store these in extra_data JSON field if your model has it
                        # Otherwise they'll be ignored but the core vitals will match
                        extra_data=json.dumps({
                            "fio2": fio2, 
                            "wbc_count": wbc_count,
                            "lactate": lactate,
                            "blood_glucose": blood_glucose,
                            "ecg_signal": "dummy_waveform_data"
                        }) if hasattr(PatientVitalSign, 'extra_data') else None,
                        recorded_by=random.choice([2, 3]),  # doctor or nurse
                        recorded_at=recorded_at
                    )
                    db.session.add(vital)
            
            db.session.commit()
            print("✅ Vital signs created successfully!")
            
            print("📋 Creating medical history...")
            
            # Create sample medical history for some patients
            conditions = [
                'Hypertension', 'Diabetes Type 2', 'Asthma', 'Pneumonia', 
                'Broken Arm', 'Appendicitis', 'Heart Attack', 'Stroke',
                'Allergic Reaction', 'COVID-19'
            ]
            
            for patient in random.sample(patients, 8):  # Only add history for 8 random patients
                history = PatientMedicalHistory(
                    patient_id=patient.patient_id,
                    condition=random.choice(conditions),
                    diagnosis_date=(patient.admission_date - timedelta(days=random.randint(1, 10))).date(),
                    treatment="Standard protocol treatment",
                    medication="Various medications as prescribed",
                    notes="Patient responding well to treatment",
                    recorded_by=2,  # doctor
                    recorded_at=patient.admission_date
                )
                db.session.add(history)
            
            db.session.commit()
            print("✅ Medical history created successfully!")
            
            print("\n🎉 Database initialization complete!")
            print("\n📝 Default Login Credentials:")
            print("   Admin:     username=admin,     password=admin")
            print("   Doctor:    username=doctor,    password=doctor")
            print("   Nurse:     username=nurse,     password=nurse")
            print("   Tech:      username=tech,      password=tech")
            print(f"\n📊 Created {User.query.count()} users and {Patient.query.count()} patients")
            
        except Exception as e:
            print(f"❌ Error during database initialization: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    init_database()

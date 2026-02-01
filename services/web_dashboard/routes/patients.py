from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime

from models.patient import Patient, PatientLocation, PatientVitalSign, PatientMedicalHistory, db

patients = Blueprint('patients', __name__)

# Import the API utility
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.api import main_host_api

# Patient views (HTML pages)
@patients.route('/')
def list_patients():
    """Show list of all patients (public, no login required)"""
    # Try to get data from main host first
    dashboard_data = main_host_api.get_dashboard_data()
    patients_list = []
    
    if dashboard_data and dashboard_data.get('status') == 'success':
        # Convert main host data to patient format
        data = dashboard_data.get('data', {})
        seen_patients = set()
        
        for key, patient_data in data.items():
            if isinstance(patient_data, dict):
                patient_id = patient_data.get('patient', 'Unknown')
                if patient_id not in seen_patients:
                    seen_patients.add(patient_id)
                    
                    # Create a patient-like object for template
                    patient_info = {
                        'patient_id': patient_id,
                        'first_name': f'Patient {patient_id}',  # Better naming
                        'last_name': '',
                        'hospital': patient_data.get('hospital', 'Unknown'),
                        'dept': patient_data.get('dept', 'Unknown'),
                        'ward': patient_data.get('ward', 'Unknown'),
                        'status': 'active',
                        'heart_rate': patient_data.get('heart_rate'),
                        'spo2': patient_data.get('spo2'),
                        'bp_systolic': patient_data.get('bp_systolic'),
                        'bp_diastolic': patient_data.get('bp_diastolic'),
                        'respiratory_rate': patient_data.get('respiratory_rate'),
                        'temperature': patient_data.get('temperature'),
                        'etco2': patient_data.get('etco2'),
                        'fio2': patient_data.get('fio2'),
                        'blood_glucose': patient_data.get('blood_glucose'),
                        'lactate': patient_data.get('lactate'),
                        'wbc_count': patient_data.get('wbc_count'),
                        'anomaly_score': patient_data.get('anomaly_score', 0),
                        'timestamp': patient_data.get('timestamp')
                    }
                    patients_list.append(patient_info)
    
    # If no data from main host, show empty list (consistent with home page)
    if not patients_list:
        patients_list = []
    
    return render_template('patients/list.html', patients=patients_list)

@patients.route('/<patient_id>')
def view_patient(patient_id):
    """Show details for a specific patient (public, no login required)"""
    # Try to get data from main host first
    patient_data = main_host_api.get_patient_data(patient_id)
    
    if patient_data and patient_data.get('status') == 'success':
        # Use main host data
        data = patient_data.get('data', {})
        # Find the most recent data for this patient
        patient_info = None
        for key, patient_record in data.items():
            if isinstance(patient_record, dict) and str(patient_record.get('patient')) == str(patient_id):
                patient_info = {
                    'patient_id': patient_id,
                    'first_name': f'Patient {patient_id}',
                    'last_name': '',
                    'hospital': patient_record.get('hospital', 'Unknown'),
                    'dept': patient_record.get('dept', 'Unknown'),
                    'ward': patient_record.get('ward', 'Unknown'),
                    'heart_rate': patient_record.get('heart_rate'),
                    'spo2': patient_record.get('spo2'),
                    'bp_systolic': patient_record.get('bp_systolic'),
                    'bp_diastolic': patient_record.get('bp_diastolic'),
                    'temperature': patient_record.get('temperature'),
                    'anomaly_score': patient_record.get('anomaly_score', 0),
                    'timestamp': patient_record.get('timestamp')
                }
                break
        
        if patient_info:
            return render_template('patients/view.html', patient=patient_info)
    
    # Fallback to database or show error
    try:
        patient = Patient.query.get_or_404(int(patient_id))
        latest_vitals = patient.get_recent_vitals(1)
        latest_vital = latest_vitals[0] if latest_vitals else None
        medical_history = PatientMedicalHistory.query.filter_by(patient_id=patient_id).order_by(PatientMedicalHistory.diagnosis_date.desc()).all()
        location_history = PatientLocation.query.filter_by(patient_id=patient_id).order_by(PatientLocation.assigned_at.desc()).all()
        return render_template('patients/view.html', 
                              patient=patient, 
                              latest_vital=latest_vital,
                              medical_history=medical_history,
                              location_history=location_history)
    except:
        # Patient not found
        return render_template('patients/view.html', patient=None, error=f"Patient {patient_id} not found")

@patients.route('/<int:patient_id>/vitals')
def patient_vitals(patient_id):
    """Show vital sign history for a patient (public, no login required)"""
    patient = Patient.query.get_or_404(patient_id)
    # Get all vitals, ordered by most recent first
    vitals = PatientVitalSign.query.filter_by(patient_id=patient_id).order_by(PatientVitalSign.recorded_at.desc()).all()
    return render_template('patients/vitals.html', patient=patient, vitals=vitals)

@patients.route('/<int:patient_id>/vitals/add', methods=['GET', 'POST'])
@login_required
def add_vitals(patient_id):
    """Add new vital signs for a patient"""
    if not current_user.has_permission('add_vitals'):
        flash('You do not have permission to add vital signs.')
        return redirect(url_for('patients.view_patient', patient_id=patient_id))
        
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        # Create new vital sign record
        new_vitals = PatientVitalSign(
            patient_id=patient_id,
            heart_rate=request.form.get('heart_rate', type=float),
            spo2=request.form.get('spo2', type=float),
            bp_systolic=request.form.get('bp_systolic', type=float),
            bp_diastolic=request.form.get('bp_diastolic', type=float),
            respiratory_rate=request.form.get('respiratory_rate', type=float),
            temperature=request.form.get('temperature', type=float),
            etco2=request.form.get('etco2', type=float),
            recorded_by=current_user.user_id,
            recorded_at=datetime.utcnow()
        )
        
        db.session.add(new_vitals)
        db.session.commit()
        
        flash('Vital signs recorded successfully.')
        return redirect(url_for('patients.patient_vitals', patient_id=patient_id))
        
    return render_template('patients/add_vitals.html', patient=patient)

@patients.route('/create', methods=['GET', 'POST'])
@login_required
def create_patient():
    """Create a new patient record"""
    if not current_user.has_permission('edit_patients'):
        flash('You do not have permission to create patients.')
        return redirect(url_for('patients.list_patients'))
        
    if request.method == 'POST':
        # Create new patient record
        new_patient = Patient(
            mrn=request.form.get('mrn'),
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date(),
            gender=request.form.get('gender'),
            blood_type=request.form.get('blood_type'),
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            emergency_contact=request.form.get('emergency_contact'),
            emergency_phone=request.form.get('emergency_phone'),
            admission_date=datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d %H:%M') if request.form.get('admission_date') else None,
            status=request.form.get('status', 'admitted'),
            notes=request.form.get('notes')
        )
        
        db.session.add(new_patient)
        db.session.commit()
        
        # Add initial location if provided
        if request.form.get('hospital') and request.form.get('department') and request.form.get('ward'):
            location = PatientLocation(
                patient_id=new_patient.patient_id,
                hospital=request.form.get('hospital'),
                department=request.form.get('department'),
                ward=request.form.get('ward'),
                bed=request.form.get('bed'),
                assigned_at=datetime.utcnow(),
                active=True
            )
            
            db.session.add(location)
            db.session.commit()
            
        flash(f'Patient {new_patient.get_full_name()} created successfully.')
        return redirect(url_for('patients.view_patient', patient_id=new_patient.patient_id))
        
    return render_template('patients/create.html')

@patients.route('/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    """Edit an existing patient record"""
    if not current_user.has_permission('edit_patients'):
        flash('You do not have permission to edit patients.')
        return redirect(url_for('patients.view_patient', patient_id=patient_id))
        
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        # Update patient record
        patient.mrn = request.form.get('mrn')
        patient.first_name = request.form.get('first_name')
        patient.last_name = request.form.get('last_name')
        patient.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date()
        patient.gender = request.form.get('gender')
        patient.blood_type = request.form.get('blood_type')
        patient.address = request.form.get('address')
        patient.phone = request.form.get('phone')
        patient.email = request.form.get('email')
        patient.emergency_contact = request.form.get('emergency_contact')
        patient.emergency_phone = request.form.get('emergency_phone')
        patient.status = request.form.get('status')
        patient.notes = request.form.get('notes')
        
        # Handle admission/discharge dates
        if request.form.get('admission_date'):
            patient.admission_date = datetime.strptime(request.form.get('admission_date'), '%Y-%m-%d %H:%M')
        
        if request.form.get('discharge_date'):
            patient.discharge_date = datetime.strptime(request.form.get('discharge_date'), '%Y-%m-%d %H:%M')
            
            # If discharged, mark all locations as inactive
            if patient.status == 'discharged':
                for location in patient.locations:
                    location.active = False
        
        patient.updated_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Patient {patient.get_full_name()} updated successfully.')
        return redirect(url_for('patients.view_patient', patient_id=patient_id))
        
    return render_template('patients/edit.html', patient=patient)

@patients.route('/<int:patient_id>/location', methods=['GET', 'POST'])
@login_required
def update_location(patient_id):
    """Update a patient's location"""
    if not current_user.has_permission('edit_patients'):
        flash('You do not have permission to update patient location.')
        return redirect(url_for('patients.view_patient', patient_id=patient_id))
        
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        # Mark all existing locations as inactive
        for location in patient.locations:
            location.active = False
            
        # Create new location
        new_location = PatientLocation(
            patient_id=patient_id,
            hospital=request.form.get('hospital'),
            department=request.form.get('department'),
            ward=request.form.get('ward'),
            bed=request.form.get('bed'),
            assigned_at=datetime.utcnow(),
            active=True
        )
        
        db.session.add(new_location)
        db.session.commit()
        
        flash(f'Patient location updated successfully.')
        return redirect(url_for('patients.view_patient', patient_id=patient_id))
        
    return render_template('patients/update_location.html', patient=patient)

@patients.route('/<int:patient_id>/medical-history/add', methods=['GET', 'POST'])
@login_required
def add_medical_history(patient_id):
    """Add medical history for a patient"""
    if not current_user.has_permission('edit_patients'):
        flash('You do not have permission to add medical history.')
        return redirect(url_for('patients.view_patient', patient_id=patient_id))
        
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        # Create new medical history record
        history = PatientMedicalHistory(
            patient_id=patient_id,
            condition=request.form.get('condition'),
            diagnosis_date=datetime.strptime(request.form.get('diagnosis_date'), '%Y-%m-%d').date() if request.form.get('diagnosis_date') else None,
            treatment=request.form.get('treatment'),
            medication=request.form.get('medication'),
            notes=request.form.get('notes'),
            recorded_by=current_user.user_id,
            recorded_at=datetime.utcnow()
        )
        
        db.session.add(history)
        db.session.commit()
        
        flash('Medical history added successfully.')
        return redirect(url_for('patients.view_patient', patient_id=patient_id))
        
    return render_template('patients/add_medical_history.html', patient=patient)

# API endpoints (JSON responses)
@patients.route('/api')
@login_required
def api_list_patients():
    """API endpoint to get a list of all patients"""
    if not current_user.has_permission('view_patients'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    all_patients = Patient.query.all()
    patients_list = [patient.to_dict() for patient in all_patients]
    
    return jsonify({
        'status': 'success',
        'count': len(patients_list),
        'patients': patients_list
    })

@patients.route('/api/<int:patient_id>')
@login_required
def api_get_patient(patient_id):
    """API endpoint to get details for a specific patient"""
    if not current_user.has_permission('view_patients'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    patient = Patient.query.get_or_404(patient_id)
    
    # Get detailed patient information including latest vitals
    patient_data = patient.to_dict()
    
    # Add latest vital signs if available
    latest_vitals = patient.get_recent_vitals(1)
    patient_data['latest_vitals'] = latest_vitals[0].to_dict() if latest_vitals else None
    
    return jsonify({
        'status': 'success',
        'patient': patient_data
    })

@patients.route('/api/<int:patient_id>/vitals')
@login_required
def api_get_patient_vitals(patient_id):
    """API endpoint to get vital sign history for a patient"""
    if not current_user.has_permission('view_vitals'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    # Check if patient exists
    patient = Patient.query.get_or_404(patient_id)
    
    # Get limit parameter (default to 10)
    limit = request.args.get('limit', 10, type=int)
    
    # Get vitals, ordered by most recent first
    vitals = PatientVitalSign.query.filter_by(patient_id=patient_id)\
        .order_by(PatientVitalSign.recorded_at.desc())\
        .limit(limit).all()
    
    vitals_list = [vital.to_dict() for vital in vitals]
    
    return jsonify({
        'status': 'success',
        'patient_id': patient_id,
        'patient_name': patient.get_full_name(),
        'count': len(vitals_list),
        'vitals': vitals_list
    })

@patients.route('/api/<int:patient_id>/vitals', methods=['POST'])
@login_required
def api_add_patient_vitals(patient_id):
    """API endpoint to add new vital signs for a patient"""
    if not current_user.has_permission('add_vitals'):
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403
        
    # Check if patient exists
    patient = Patient.query.get_or_404(patient_id)
    
    # Get data from request
    data = request.json
    
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'}), 400
    
    # Create new vital sign record
    new_vitals = PatientVitalSign(
        patient_id=patient_id,
        heart_rate=data.get('heart_rate'),
        spo2=data.get('spo2'),
        bp_systolic=data.get('bp_systolic'),
        bp_diastolic=data.get('bp_diastolic'),
        respiratory_rate=data.get('respiratory_rate'),
        temperature=data.get('temperature'),
        etco2=data.get('etco2'),
        recorded_by=current_user.user_id,
        recorded_at=datetime.utcnow()
    )
    
    db.session.add(new_vitals)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': 'Vital signs recorded successfully',
        'vital_id': new_vitals.vital_id,
        'patient_id': patient_id,
        'patient_name': patient.get_full_name()
    })

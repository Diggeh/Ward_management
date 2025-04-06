from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from database import db
from models import Patient, Ward, Bed, Admission, Role, User, MedicalRecord
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from forms import AdmissionForm

main_bp = Blueprint('main', __name__)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    try:
        seven_days_ago_dt = datetime.utcnow() - timedelta(days=7)

        recent_admissions = Admission.query.options(joinedload(Admission.patient))\
            .filter(Admission.AdmissionDate >= seven_days_ago_dt)\
            .order_by(Admission.AdmissionDate.desc()).all()

        recent_discharges = Admission.query.options(joinedload(Admission.patient))\
            .filter(Admission.DischargeDate.isnot(None),
                    Admission.DischargeDate >= seven_days_ago_dt)\
            .order_by(Admission.DischargeDate.desc()).all()

        wards = Ward.query.order_by(Ward.WardName.asc()).all()

        return render_template('dashboard.html',
                               user=current_user,
                               recent_admissions=recent_admissions,
                               recent_discharges=recent_discharges,
                               wards=wards)

    except Exception as e:
        print(f"Error loading dashboard data: {e}")
        return render_template('error.html', error_message="Could not load dashboard data."), 500

@main_bp.route('/admission', methods=['GET', 'POST'])
@login_required
def admission():    
    # Load doctors
    doctor_role = Role.query.filter_by(role_name='doctor').first()
    doctors = User.query.filter_by(role_id=doctor_role.id).all() if doctor_role else []
    
    form = AdmissionForm()
    
    # Set dropdown choices
    form.ward.choices = [(w.WardID, w.WardName) for w in Ward.query.order_by(Ward.WardName).all()]
    form.doctor.choices = [(d.id, f"Dr. {d.username}") for d in doctors]
    
    # Handle AJAX request for beds
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        ward_id = request.form.get('ward')
        available_beds = Bed.query.filter_by(
            WardID=ward_id,
            BedStatus='Vacant'
        ).all()
        return jsonify([{'id': bed.BedID, 'number': bed.BedNumber} for bed in available_beds])
    
    # Handle form submission
    if form.validate_on_submit():
        try:
            # Verify bed is still available
            bed = Bed.query.get(form.bed.data)
            if not bed or bed.BedStatus != 'Vacant':
                flash('Selected bed is no longer available', 'danger')
                return redirect(url_for('main.admission'))
            
            # Create patient
            patient = Patient(
                FirstName=form.first_name.data.strip(),  # Fixed typo: stript() -> strip()
                LastName=form.last_name.data.strip(),
                Gender=form.gender.data,
                DateOfBirth=form.dob.data,
                ContactNumber=form.contact_number.data,
                EmergencyContact=form.emergency_contact.data,
                Address=form.address.data
            )
            db.session.add(patient)
            db.session.flush()

            # Update bed status
            bed.BedStatus = 'Occupied'
            db.session.add(bed)

            # Create admission - using selected doctor from dropdown
            selected_doctor = User.query.get(form.doctor.data)
            admission = Admission(
                PatientID=patient.PatientID,
                BedID=form.bed.data,
                AdmissionDate=datetime.now(),
                Diagnosis=form.diagnosis.data,
                DoctorInCharge=selected_doctor.username  # Using selected doctor
            )
            db.session.add(admission)
            db.session.commit()

            flash(f'{patient.FirstName} {patient.LastName} admitted successfully!', 'success')  # Fixed variable reference
            return redirect(url_for('main.admission'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error admitting patient: {str(e)}', 'danger')

    return render_template(
        'admission.html',
        form=form,
    )

@main_bp.route('/wards')
@login_required  # Add if you want it protected
def wards():

    return render_template('wards.html')

@main_bp.route('/patients')
@login_required  # Add if you want it protected
def patients():
    return render_template('patients.html', user=current_user)

@main_bp.route('/search-patients')
@login_required
def search_patients():
    search_term = request.args.get('query', '')
    
    # Search for patients
    if search_term:
        patients = Patient.query.filter(
                or_(
                    Patient.FirstName.ilike(f'%{search_term}%'),
                    Patient.LastName.ilike(f'%{search_term}%')
                )
            ).order_by(Patient.LastName.asc()).all()
    else:
        # If there's no search term, return all patients
        patients = Patient.query.order_by(Patient.LastName.asc()).all()
            
    # JSON formatting
    patients_data = []
    for patient in patients:
        patients_data.append({
            'patient_id': patient.PatientID,
            'patient_name': f"{patient.FirstName} {patient.LastName}",
            'gender': 'Male' if patient.Gender == 1 else 'Female' if patient.Gender == 2 else 'Other',
            'dob': patient.DateOfBirth.strftime('%Y-%m-%d') if patient.DateOfBirth else '',
            'contact': patient.ContactNumber,
            'emergency_contact': patient.EmergencyContact,
            'address': patient.Address
        })
    
    return jsonify(patients_data)

@main_bp.route('/get-patient/<int:patient_id>')
@login_required
def get_patient(patient_id):
    patient = Patient.query.get(patient_id)
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    return jsonify({
        'patient_id': patient.PatientID,
        'first_name': patient.FirstName,
        'last_name': patient.LastName,
        'gender': patient.Gender,
        'dob': patient.DateOfBirth.strftime('%Y-%m-%d') if patient.DateOfBirth else '',
        'contact': patient.ContactNumber,
        'emergency_contact': patient.EmergencyContact,
        'address': patient.Address
    })

@main_bp.route('/update-patient/<int:patient_id>', methods=['POST'])
@login_required
def update_patient(patient_id):
    patient = Patient.query.get(patient_id)
    
    if not patient:
        return jsonify({'error': 'Patient not found'}), 404
    
    data = request.json
    
    try:
        # Update fields from form
        patient.FirstName = data.get('first_name')
        patient.LastName = data.get('last_name')
        patient.Gender = data.get('gender')
        patient.DateOfBirth = datetime.strptime(data.get('dob'), '%Y-%m-%d') if data.get('dob') else None
        patient.ContactNumber = data.get('contact')
        patient.EmergencyContact = data.get('emergency_contact')
        patient.Address = data.get('address')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Patient information updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/medical-records')
@login_required
def medical_records():
    # Get all medical records by default
    records = db.session.query(MedicalRecord, Patient)\
        .join(Patient, MedicalRecord.PatientID == Patient.PatientID)\
        .order_by(MedicalRecord.RecordDate.desc())\
        .all()
    
    return render_template('medical_records.html', 
                           records=records,
                           user=current_user)
    
@main_bp.route('/search-records')
@login_required
def search_records():
    search_term = request.args.get('query', '')
    
    # Search 
    if search_term:
        records = db.session.query(MedicalRecord, Patient)\
            .join(Patient, MedicalRecord.PatientID == Patient.PatientID)\
            .filter(
                or_(
                    Patient.FirstName.ilike(f'%{search_term}%'),
                    Patient.LastName.ilike(f'%{search_term}%')
                )
            )\
            .order_by(MedicalRecord.RecordDate.desc())\
            .all()
    else:
        # If there's no search, then return every record
        records = db.session.query(MedicalRecord, Patient)\
            .join(Patient, MedicalRecord.PatientID == Patient.PatientID)\
            .order_by(MedicalRecord.RecordDate.desc())\
            .all()
            
     # JSON formatting
    records_data = []
    for record, patient in records:
        records_data.append({
            'record_id': record.RecordID,
            'patient_id': patient.PatientID,
            'patient_name': f"{patient.FirstName} {patient.LastName}",
            'record_date': record.RecordDate.strftime('%Y-%m-%d') if record.RecordDate else '',
            'conditions': record.Conditions,
            'allergies': record.Allergies,
            'medications': record.Medications,
            'notes': record.Notes
        })
    
    return jsonify(records_data)          

@main_bp.route('/get-record/<int:record_id>')
@login_required
def get_record(record_id):
    record = db.session.query(MedicalRecord, Patient)\
        .join(Patient, MedicalRecord.PatientID == Patient.PatientID)\
        .filter(MedicalRecord.RecordID == record_id)\
        .first()
    
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    
    record_obj, patient = record
    
    return jsonify({
        'record_id': record_obj.RecordID,
        'patient_id': patient.PatientID,
        'patient_name': f"{patient.FirstName} {patient.LastName}",
        'record_date': record_obj.RecordDate.strftime('%Y-%m-%d') if record_obj.RecordDate else '',
        'conditions': record_obj.Conditions,
        'allergies': record_obj.Allergies,
        'medications': record_obj.Medications,
        'notes': record_obj.Notes
    })

@main_bp.route('/update-record/<int:record_id>', methods=['POST'])
@login_required
def update_record(record_id):
    record = MedicalRecord.query.get(record_id)
    
    if not record:
        return jsonify({'error': 'Record not found'}), 404
    
    data = request.json
    
    try:
        # Update fields from form
        record.RecordDate = datetime.strptime(data.get('record_date'), '%Y-%m-%d') if data.get('record_date') else None
        record.Allergies = data.get('allergies')
        record.Conditions = data.get('conditions')
        record.Medications = data.get('medications')
        record.Notes = data.get('notes')
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Record updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@main_bp.route('/admin')
@login_required
def admin_page():
    if not current_user.role_id or current_user.role_id != 1:
        flash('Access denied. You must be an administrator to view this page.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('admin.html', user=current_user)
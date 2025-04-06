from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from database import db
from models import Patient, Ward, Bed, Admission, Role, User, MedicalRecord
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

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
        
        # Calculate bed statistics for each ward
        for ward in wards:
            total_beds = len(ward.beds)
            occupied_beds = sum(1 for bed in ward.beds if bed.BedStatus == 'Occupied')
            ward.capacity_display = f"{occupied_beds}/{total_beds}"

        return render_template('dashboard.html',
                               user=current_user,
                               recent_admissions=recent_admissions,
                               recent_discharges=recent_discharges,
                               wards=wards,
                               current_date=datetime.now().strftime('%Y-%m-%d'))

    except Exception as e:
        print(f"Error loading dashboard data: {e}")
        return render_template('error.html', error_message="Could not load dashboard data."), 500

@main_bp.route('/admission', methods=['GET', 'POST'])
@login_required
def admission():
    # Load doctors directly by role_id=2 (doctors)
    doctors = User.query.filter_by(role_id=2).all()
    
    # Load wards for dropdown
    wards = Ward.query.order_by(Ward.WardName.asc()).all()
    
    # Handle AJAX request for beds
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        ward_id = request.form.get('ward')
        available_beds = Bed.query.filter_by(
            WardID=ward_id,
            BedStatus='Vacant'
        ).all()
        return jsonify([{'id': bed.BedID, 'number': bed.BedNumber} for bed in available_beds])
    
    # Handle form submission
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            gender_code = request.form.get('gender')
            dob = request.form.get('dob')
            contact_number = request.form.get('contact_number')
            emergency_contact = request.form.get('emergency_contact')
            address = request.form.get('address')
            doctor_id = request.form.get('doctor')
            ward_id = request.form.get('ward')
            bed_id = request.form.get('bed')
            diagnosis = request.form.get('diagnosis')
            
            # Get medical record data (add these fields to your form)
            allergies = request.form.get('allergies', '')
            conditions = request.form.get('conditions', '')
            medications = request.form.get('medications', '')
            notes = request.form.get('notes', '')
            
            # Convert gender code to text value
            gender_map = {'1': 'Male', '2': 'Female', '3': 'Other'}
            gender = gender_map.get(gender_code, None)
            
            # Validate required fields
            errors = []
            if not first_name:
                errors.append("First name is required")
            if not last_name:
                errors.append("Last name is required")
            if not gender:
                errors.append("Gender is required")
            if not dob:
                errors.append("Date of birth is required")
            if not doctor_id:
                errors.append("Doctor is required")
            if not ward_id:
                errors.append("Ward is required")
            if not bed_id:
                errors.append("Bed is required")
            
            if errors:
                for error in errors:
                    flash(error, 'danger')
                return render_template(
                    'admission.html',
                    doctors=doctors,
                    wards=wards,
                    form_data=request.form
                )
            
            # Verify bed is still available
            bed = Bed.query.get(bed_id)
            if not bed or bed.BedStatus != 'Vacant':
                flash('Selected bed is no longer available', 'danger')
                return redirect(url_for('main.admission'))
            
            # Convert data types
            dob = datetime.strptime(dob, '%Y-%m-%d')
            
            # Create patient
            patient = Patient(
                FirstName=first_name,
                LastName=last_name,
                Gender=gender,  # Use the mapped text value
                DateOfBirth=dob,
                ContactNumber=contact_number,
                EmergencyContact=emergency_contact,
                Address=address
            )
            db.session.add(patient)
            db.session.flush()  # Flush to get the PatientID

            # Create medical record
            medical_record = MedicalRecord(
                PatientID=patient.PatientID,
                RecordDate=datetime.now(),
                Allergies=allergies,
                Conditions=conditions or diagnosis,  # Use diagnosis as conditions if not provided
                Medications=medications,
                Notes=notes
            )
            db.session.add(medical_record)

            # Update bed status
            bed.BedStatus = 'Occupied'
            db.session.add(bed)

            # Create admission
            selected_doctor = User.query.get(doctor_id)
            admission = Admission(
                PatientID=patient.PatientID,
                BedID=bed_id,
                AdmissionDate=datetime.now(),
                Diagnosis=diagnosis,
                DoctorInCharge=selected_doctor.username,
                doctor_id=doctor_id
            )
            db.session.add(admission)
            db.session.commit()

            flash(f'{patient.FirstName} {patient.LastName} admitted successfully!', 'success')
            return redirect(url_for('main.admission'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error admitting patient: {str(e)}', 'danger')

    return render_template(
        'admission.html',
        doctors=doctors,
        wards=wards,
        form_data={}
    )

@main_bp.route('/wards')
@login_required  
def wards():
     return render_template('wards.html', user=current_user)

@main_bp.route('/patients')
@login_required  
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
        # Return all patients
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
    
@main_bp.route('/discharge-patient/<int:patient_id>', methods=['POST'])
@login_required
def discharge_patient(patient_id):
    try:
        # Find active admission for this patient
        active_admission = Admission.query.filter_by(
            PatientID=patient_id, 
            DischargeDate=None
        ).first()
        
        if not active_admission:
            return jsonify({'error': 'No active admission found for this patient'}), 404
        
        # Update admission with discharge date
        active_admission.DischargeDate = datetime.now()
        
        # Update bed status to vacant
        bed = Bed.query.get(active_admission.BedID)
        if bed:
            bed.BedStatus = 'Vacant'
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Patient discharged successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/delete-patient/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    try:
        # Check if patient exists
        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        # Check if patient has an active admission
        active_admission = Admission.query.filter_by(
            PatientID=patient_id, 
            DischargeDate=None
        ).first()
        
        if active_admission:
            return jsonify({
                'error': 'Cannot delete a patient with an active admission. Please discharge the patient first.'
            }), 400
        
        # Delete medical records associated with the patient
        MedicalRecord.query.filter_by(PatientID=patient_id).delete()
        
        # Delete admission history if any
        Admission.query.filter_by(PatientID=patient_id).delete()
        
        # Delete the patient
        db.session.delete(patient)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Patient deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@main_bp.route('/medical-records')
@login_required
def medical_records():
    # Check if a specific patient is requested
    patient_id = request.args.get('patient')
    
    query = db.session.query(MedicalRecord, Patient)\
        .join(Patient, MedicalRecord.PatientID == Patient.PatientID)
    
    # Filter by patient if specified
    if patient_id:
        query = query.filter(Patient.PatientID == patient_id)
    
    # Get the records
    records = query.order_by(MedicalRecord.RecordDate.desc()).all()
    
    return render_template('medical_records.html', 
                           records=records,
                           user=current_user,
                           patient_filter=patient_id)
    
@main_bp.route('/search-records')
@login_required
def search_records():
    search_term = request.args.get('query', '')
    patient_id = request.args.get('patient')
    
    # Base query
    query = db.session.query(MedicalRecord, Patient)\
        .join(Patient, MedicalRecord.PatientID == Patient.PatientID)
    
    # Apply filters
    if patient_id:
        # Filter by specific patient ID
        query = query.filter(Patient.PatientID == patient_id)
    elif search_term:
        # Search by name
        query = query.filter(
            or_(
                Patient.FirstName.ilike(f'%{search_term}%'),
                Patient.LastName.ilike(f'%{search_term}%')
            )
        )
    
    # Execute query with ordering
    records = query.order_by(MedicalRecord.RecordDate.desc()).all()
            
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
        # Update fields 
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

@main_bp.route('/get-wards')
@login_required
def get_wards():
    try:
        wards = Ward.query.order_by(Ward.WardName.asc()).all()
        
        # Calculate occupied and vacant beds
        wards_data = []
        for ward in wards:
            total_beds = len(ward.beds)
            occupied_beds = sum(1 for bed in ward.beds if bed.BedStatus == 'Occupied')
            vacant_beds = sum(1 for bed in ward.beds if bed.BedStatus == 'Vacant')
            
            wards_data.append({
                'ward_id': ward.WardID,
                'ward_name': ward.WardName,
                'ward_type': ward.WardType,
                'ward_capacity': ward.WardCapacity,
                'total_beds': total_beds,
                'occupied_beds': occupied_beds,
                'vacant_beds': vacant_beds
            })
        
        return jsonify(wards_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/search-wards')
@login_required
def search_wards():
    search_term = request.args.get('query', '')
    
    try:
        if search_term:
            wards = Ward.query.filter(
                Ward.WardName.ilike(f'%{search_term}%')
            ).order_by(Ward.WardName.asc()).all()
        else:
            wards = Ward.query.order_by(Ward.WardName.asc()).all()
        
        # Calculate occupied and vacant beds
        wards_data = []
        for ward in wards:
            total_beds = len(ward.beds)
            occupied_beds = sum(1 for bed in ward.beds if bed.BedStatus == 'Occupied')
            vacant_beds = sum(1 for bed in ward.beds if bed.BedStatus == 'Vacant')
            
            wards_data.append({
                'ward_id': ward.WardID,
                'ward_name': ward.WardName,
                'ward_type': ward.WardType,
                'ward_capacity': ward.WardCapacity,
                'total_beds': total_beds,
                'occupied_beds': occupied_beds,
                'vacant_beds': vacant_beds
            })
        
        return jsonify(wards_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/get-ward-beds/<int:ward_id>')
@login_required
def get_ward_beds(ward_id):
    try:
        beds = Bed.query.filter_by(WardID=ward_id).order_by(Bed.BedNumber.asc()).all()
        
        beds_data = []
        for bed in beds:
            # Get patient information if bed is occupied
            patient_name = None
            if bed.BedStatus == 'Occupied':
                # Find the active admission for this bed
                admission = Admission.query.filter_by(
                    BedID=bed.BedID, 
                    DischargeDate=None
                ).first()
                
                if admission:
                    patient = Patient.query.get(admission.PatientID)
                    if patient:
                        patient_name = f"{patient.FirstName} {patient.LastName}"
            
            beds_data.append({
                'bed_id': bed.BedID,
                'bed_number': bed.BedNumber,
                'bed_status': bed.BedStatus,
                'patient_name': patient_name
            })
        
        return jsonify(beds_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/get-bed/<int:bed_id>')
@login_required
def get_bed(bed_id):
    try:
        bed = Bed.query.get(bed_id)
        
        if not bed:
            return jsonify({'error': 'Bed not found'}), 404
        
        bed_data = {
            'bed_id': bed.BedID,
            'ward_id': bed.WardID,
            'bed_number': bed.BedNumber,
            'bed_status': bed.BedStatus,
            'patient_info': None
        }
        
        # Get patient information if bed is occupied
        if bed.BedStatus == 'Occupied':
            # Find the active admission for this bed
            admission = Admission.query.filter_by(
                BedID=bed.BedID, 
                DischargeDate=None
            ).first()
            
            if admission:
                patient = Patient.query.get(admission.PatientID)
                if patient:
                    bed_data['patient_info'] = {
                        'patient_id': patient.PatientID,
                        'name': f"{patient.FirstName} {patient.LastName}",
                        'admission_date': admission.AdmissionDate.strftime('%Y-%m-%d'),
                        'doctor': admission.DoctorInCharge,
                        'diagnosis': admission.Diagnosis
                    }
        
        return jsonify(bed_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/update-bed/<int:bed_id>', methods=['POST'])
@login_required
def update_bed(bed_id):
    try:
        bed = Bed.query.get(bed_id)
        
        if not bed:
            return jsonify({'error': 'Bed not found'}), 404
        
        data = request.json
        previous_status = bed.BedStatus
        new_status = data.get('bed_status')
        
        # Update bed status
        bed.BedStatus = new_status
        
        # If bed was occupied and now it's not, discharge the patient
        if previous_status == 'Occupied' and new_status != 'Occupied':
            # Find the active admission for this bed
            admission = Admission.query.filter_by(
                BedID=bed.BedID, 
                DischargeDate=None
            ).first()
            
            if admission:
                # Set discharge date to today
                admission.DischargeDate = datetime.now()
                
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Bed updated successfully',
            'previous_status': previous_status,
            'new_status': new_status
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/get-ward/<int:ward_id>')
@login_required
def get_ward(ward_id):
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access'}), 403
        
    try:
        ward = Ward.query.get(ward_id)
        
        if not ward:
            return jsonify({'error': 'Ward not found'}), 404
        
        return jsonify({
            'ward_id': ward.WardID,
            'ward_name': ward.WardName,
            'ward_type': ward.WardType,
            'ward_capacity': ward.WardCapacity
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/create-ward', methods=['POST'])
@login_required
def create_ward():
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access'}), 403
        
    try:
        data = request.json
        
        # Create new ward
        ward = Ward(
            WardName=data.get('ward_name'),
            WardType=data.get('ward_type'),
            WardCapacity=data.get('ward_capacity')
        )
        
        db.session.add(ward)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Ward created successfully',
            'ward_id': ward.WardID
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/update-ward/<int:ward_id>', methods=['POST'])
@login_required
def update_ward(ward_id):
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access'}), 403
        
    try:
        ward = Ward.query.get(ward_id)
        
        if not ward:
            return jsonify({'error': 'Ward not found'}), 404
        
        data = request.json
        
        # Update ward fields
        ward.WardName = data.get('ward_name')
        ward.WardType = data.get('ward_type')
        ward.WardCapacity = data.get('ward_capacity')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Ward updated successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/delete-ward/<int:ward_id>', methods=['POST'])
@login_required
def delete_ward(ward_id):
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access'}), 403
        
    try:
        ward = Ward.query.get(ward_id)
        
        if not ward:
            return jsonify({'error': 'Ward not found'}), 404
        
        # Check if ward has any occupied beds
        occupied_beds = Bed.query.filter_by(WardID=ward_id, BedStatus='Occupied').count()
        
        if occupied_beds > 0:
            return jsonify({
                'error': f'Cannot delete ward: {occupied_beds} bed(s) are currently occupied'
            }), 400
        
        # Delete all beds in this ward
        Bed.query.filter_by(WardID=ward_id).delete()
        
        # Delete the ward
        db.session.delete(ward)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Ward deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/create-bed', methods=['POST'])
@login_required
def create_bed():
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access'}), 403
        
    try:
        data = request.json
        
        # Check if bed number already exists in ward
        existing_bed = Bed.query.filter_by(
            WardID=data.get('ward_id'),
            BedNumber=data.get('bed_number')
        ).first()
        
        if existing_bed:
            return jsonify({
                'error': f'Bed number {data.get("bed_number")} already exists in this ward'
            }), 400
        
        # Create new bed
        bed = Bed(
            WardID=data.get('ward_id'),
            BedNumber=data.get('bed_number'),
            BedStatus=data.get('bed_status', 'Vacant')
        )
        
        db.session.add(bed)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Bed added successfully',
            'bed_id': bed.BedID
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/delete-bed/<int:bed_id>', methods=['POST'])
@login_required
def delete_bed(bed_id):
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access'}), 403
        
    try:
        bed = Bed.query.get(bed_id)
        
        if not bed:
            return jsonify({'error': 'Bed not found'}), 404
        
        # Check if bed is occupied
        if bed.BedStatus == 'Occupied':
            return jsonify({
                'error': 'Cannot delete an occupied bed. Please discharge the patient first.'
            }), 400
        
        # Check if bed has any admission history
        has_admissions = Admission.query.filter_by(BedID=bed_id).count() > 0
        
        if has_admissions:
            return jsonify({
                'error': 'Cannot delete bed with admission history. Consider marking it as out of service instead.'
            }), 400
        
        # Delete the bed
        db.session.delete(bed)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Bed deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@main_bp.route('/users')
@login_required
def users():
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        flash('Access denied. You must be an administrator to view this page.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    return render_template('users.html', user=current_user)

@main_bp.route('/search-users')
@login_required
def search_users():
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    search_term = request.args.get('query', '')
    
    # Search for users
    if search_term:
        users = User.query.filter(
                User.username.ilike(f'%{search_term}%')
            ).order_by(User.username.asc()).all()
    else:
        # If there's no search term, return all users
        users = User.query.order_by(User.username.asc()).all()
            
    # JSON formatting
    users_data = []
    for user in users:
        role_name = user.role.role_name if user.role else 'No Role'
        users_data.append({
            'user_id': user.id,
            'username': user.username,
            'role_id': user.role_id,
            'role_name': role_name
        })
    
    return jsonify(users_data)

@main_bp.route('/get-user/<int:user_id>')
@login_required
def get_user(user_id):
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    role_name = user.role.role_name if user.role else 'No Role'
    
    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'role_id': user.role_id,
        'role_name': role_name
    })

@main_bp.route('/update-user/<int:user_id>', methods=['POST'])
@login_required
def update_user(user_id):
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.json
    
    try:
        # Update fields from form
        user.username = data.get('username')
        user.role_id = data.get('role_id')
        
        # Update password if provided
        if data.get('password'):
            from werkzeug.security import generate_password_hash
            user.password = generate_password_hash(data.get('password'))
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'User information updated successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/create-user', methods=['POST'])
@login_required
def create_user():
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    data = request.json
    
    try:
        # Check if username already exists
        existing_user = User.query.filter_by(username=data.get('username')).first()
        if existing_user:
            return jsonify({'error': 'Username already exists'}), 400
        
        # Hash the password
        from werkzeug.security import generate_password_hash
        hashed_password = generate_password_hash(data.get('password'))
        
        # Create new user
        new_user = User(
            username=data.get('username'),
            password=hashed_password,
            role_id=data.get('role_id')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'User created successfully',
            'user_id': new_user.id
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@main_bp.route('/get-roles')
@login_required
def get_roles():
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    try:
        roles = Role.query.order_by(Role.role_name).all()
        roles_data = [{'role_id': role.id, 'role_name': role.role_name} for role in roles]
        return jsonify(roles_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@main_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Check if user is admin
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Prevent self-deletion
    if user_id == current_user.id:
        return jsonify({'error': 'You cannot delete your own account'}), 400
    
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500  
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash 
from flask_login import login_required, current_user
from database import db
from models import Patient, Ward, Bed, Admission 
from datetime import date 
from sqlalchemy.orm import joinedload 
from flask import abort 

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/api/list', methods=['GET']) 
@login_required
def list_patients_api():
    patients = Patient.query.all()
    result = [{
        'PatientID': p.PatientID, 'FirstName': p.FirstName, 'LastName': p.LastName,
        'DateOfBirth': str(p.DateOfBirth), 'Gender': p.Gender, 'ContactNumber': p.ContactNumber,
        'EmergencyContact': p.EmergencyContact, 'Address': p.Address
    } for p in patients]
    return jsonify(result), 200

@patients_bp.route('/api/register', methods=['POST']) 
@login_required
def register_patient_api():

    data = request.get_json()
    if not data or 'FirstName' not in data or 'LastName' not in data or 'DateOfBirth' not in data:
         return jsonify({'error': 'Missing required fields'}), 400
    try:
        new_patient = Patient(
            FirstName=data['FirstName'], LastName=data['LastName'],
            DateOfBirth=date.fromisoformat(data['DateOfBirth']), 
            Gender=data.get('Gender'), ContactNumber=data.get('ContactNumber'),
            EmergencyContact=data.get('EmergencyContact'), Address=data.get('Address')
        )
        db.session.add(new_patient)
        db.session.commit()
        return jsonify({'message': 'Patient registered successfully', 'PatientID': new_patient.PatientID}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to register patient: {str(e)}'}), 500

@patients_bp.route('/<int:patient_id>')
@login_required
def patient_details(patient_id):

    patient = Patient.query.get_or_404(patient_id)

    admissions = Admission.query.filter_by(PatientID=patient_id)\
                                .options(joinedload(Admission.bed).joinedload(Bed.ward))\
                                .order_by(Admission.AdmissionDate.desc())\
                                .all()

    return render_template('patient_details.html',
                           patient=patient,
                           admissions=admissions)

@patients_bp.route('/admit', methods=['GET'])
@login_required
def admit_form():

    if current_user.Role not in ['Admin', 'Nurse']:
         flash('You do not have permission to admit patients.', 'danger')
         return redirect(url_for('main.dashboard'))

    patients = Patient.query.order_by(Patient.LastName).all()

    available_beds = Bed.query.filter_by(BedStatus='Available')\
                            .options(joinedload(Bed.ward))\
                            .order_by(Bed.WardID, Bed.BedNumber).all()

    return render_template('admit_form.html',
                           patients=patients,
                           available_beds=available_beds)

@patients_bp.route('/admit', methods=['POST'])
@login_required
def admit_patient():
    if current_user.Role not in ['Admin', 'Nurse']:
         flash('You do not have permission to admit patients.', 'danger')
         return redirect(url_for('main.dashboard'))

    patient_id = request.form.get('patient_id', type=int)
    bed_id = request.form.get('bed_id', type=int)
    diagnosis = request.form.get('diagnosis')
    doctor = request.form.get('doctor')

    if not patient_id or not bed_id:
        flash('Patient and Bed selection are required.', 'warning')
        return redirect(url_for('patients.admit_form'))

    try:

        bed = Bed.query.get(bed_id)
        if not bed or bed.BedStatus != 'Available':
            flash('Selected bed is not available.', 'danger')
            return redirect(url_for('patients.admit_form'))

        patient = Patient.query.get(patient_id)
        if not patient:
             flash('Selected patient does not exist.', 'danger')
             return redirect(url_for('patients.admit_form'))

        new_admission = Admission(
            PatientID=patient_id,
            BedID=bed_id,
            AdmissionDate=date.today(), 
            DischargeDate=None, 
            Diagnosis=diagnosis,
            DoctorInCharge=doctor
        )

        bed.BedStatus = 'Occupied'

        db.session.add(new_admission)

        db.session.commit()

        flash(f'Patient {patient.FirstName} {patient.LastName} admitted successfully!', 'success')
        return redirect(url_for('main.dashboard'))

    except Exception as e:
        db.session.rollback() 
        flash(f'Error admitting patient: {str(e)}', 'danger')
        return redirect(url_for('patients.admit_form'))

@patients_bp.route('/discharge/<int:admission_id>', methods=['POST'])
@login_required
def discharge_patient(admission_id):

    if current_user.Role not in ['Admin', 'Nurse', 'Doctor']: 
        flash('You do not have permission to discharge patients.', 'danger')
        return redirect(request.referrer or url_for('main.dashboard')) 

    try:
        admission = Admission.query.options(joinedload(Admission.bed)).get(admission_id)

        if not admission:
            flash('Admission record not found.', 'danger')
            abort(404) 

        if admission.DischargeDate is not None:
            flash('Patient has already been discharged from this admission.', 'warning')
            return redirect(request.referrer or url_for('main.dashboard'))

        admission.DischargeDate = date.today()

        if admission.bed: 
             admission.bed.BedStatus = 'Available'

        db.session.commit()
        flash('Patient discharged successfully!', 'success')

        return redirect(url_for('main.dashboard'))

    except Exception as e:
        db.session.rollback()
        flash(f'Error discharging patient: {str(e)}', 'danger')
        return redirect(request.referrer or url_for('main.dashboard'))

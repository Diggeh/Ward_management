from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from database import db
from models import Patient, Ward, Bed, Admission, Role, User
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
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

    return render_template('patients.html')
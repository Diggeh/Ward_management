from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from database import db
from models import Patient, Ward, Bed, Admission
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

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
    if request.method == 'POST':
        try:
            # Get form data
            patient_name = request.form.get('name')
            ward_id = request.form.get('ward')
            bed_number = request.form.get('bed')

            # Validate input
            if not all([patient_name, ward_id, bed_number]):
                flash('All fields are required', 'danger')
                return redirect(url_for('main.admission'))

            # Find or create patient
            names = patient_name.split()
            first_name = names[0]
            last_name = " ".join(names[1:]) if len(names) > 1 else ""
            patient = Patient(
                FirstName=first_name,
                LastName=last_name,
                DateOfBirth=datetime.now().date(),  # Default DOB
                Gender=0  # Default gender
            )
            db.session.add(patient)
            db.session.commit()

            # Create admission
            admission = Admission(
                PatientID=patient.PatientID,
                BedID=f"{ward_id}-{bed_number}",
                AdmissionDate=datetime.now(),
                DoctorInCharge="Dr. Smith"
            )
            db.session.add(admission)
            db.session.commit()

            flash('Patient admitted successfully!', 'success')
            return redirect(url_for('main.admission'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error admitting patient: {str(e)}', 'danger')
            return redirect(url_for('main.admission'))

    # Get data for template
    current_admissions = db.session.query(
        Admission, Patient, Ward, Bed
    ).join(Patient).join(Bed).join(Ward) \
        .filter(Admission.DischargeDate.is_(None)) \
        .order_by(Admission.AdmissionDate.desc()) \
        .all()

    all_wards = Ward.query.all()

    return render_template(
        'admission.html',
        admissions=current_admissions,
        wards=all_wards
    )
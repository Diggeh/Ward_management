from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify,
    current_app,
)
from flask_login import login_required, current_user
from database import db
from models import Patient, Ward, Bed, Admission, Role, User, MedicalRecord
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, and_
from permissions import check_permission, permission_required
from audit import audit_logger

main_bp = Blueprint("main", __name__)


@main_bp.context_processor
def inject_permissions():
    return dict(check_permission=check_permission)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    try:
        seven_days_ago_dt = datetime.utcnow() - timedelta(days=7)

        recent_admissions = (
            Admission.query.options(joinedload(Admission.patient))
            .filter(Admission.AdmissionDate >= seven_days_ago_dt)
            .order_by(Admission.AdmissionDate.desc())
            .all()
        )

        recent_discharges = (
            Admission.query.options(joinedload(Admission.patient))
            .filter(
                Admission.DischargeDate.isnot(None),
                Admission.DischargeDate >= seven_days_ago_dt,
            )
            .order_by(Admission.DischargeDate.desc())
            .all()
        )

        wards = Ward.query.order_by(Ward.WardName.asc()).all()

        for ward in wards:
            total_beds = len(ward.beds)
            occupied_beds = sum(1 for bed in ward.beds if bed.BedStatus == "Occupied")
            ward.capacity_display = f"{occupied_beds}/{total_beds}"

        return render_template(
            "dashboard.html",
            user=current_user,
            recent_admissions=recent_admissions,
            recent_discharges=recent_discharges,
            wards=wards,
            current_date=datetime.now().strftime("%Y-%m-%d"),
        )

    except Exception as e:
        print(f"Error loading dashboard data: {e}")
        return (
            render_template(
                "error.html", error_message="Could not load dashboard data."
            ),
            500,
        )


@main_bp.route("/admission", methods=["GET", "POST"])
@login_required
@permission_required("add_patient")
def admission():

    doctors = User.query.filter_by(role_id=2).all()

    wards = Ward.query.order_by(Ward.WardName.asc()).all()

    if (
        request.method == "POST"
        and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):
        ward_id = request.form.get("ward")
        available_beds = Bed.query.filter_by(WardID=ward_id, BedStatus="Vacant").all()
        return jsonify(
            [{"id": bed.BedID, "number": bed.BedNumber} for bed in available_beds]
        )

    if request.method == "POST":
        try:

            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            gender_code = request.form.get("gender")
            dob = request.form.get("dob")
            contact_number = request.form.get("contact_number")
            emergency_contact = request.form.get("emergency_contact")
            address = request.form.get("address")
            doctor_id = request.form.get("doctor")
            ward_id = request.form.get("ward")
            bed_id = request.form.get("bed")
            diagnosis = request.form.get("diagnosis")

            allergies = request.form.get("allergies", "")
            conditions = request.form.get("conditions", "")
            medications = request.form.get("medications", "")
            notes = request.form.get("notes", "")

            gender_map = {"1": "Male", "2": "Female", "3": "Other"}
            gender = gender_map.get(gender_code, None)

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
                    flash(error, "danger")
                return render_template(
                    "admission.html",
                    doctors=doctors,
                    wards=wards,
                    form_data=request.form,
                )

            bed = Bed.query.get(bed_id)
            if not bed or bed.BedStatus != "Vacant":
                flash("Selected bed is no longer available", "danger")
                return redirect(url_for("main.admission"))

            dob = datetime.strptime(dob, "%Y-%m-%d")

            patient = Patient(
                FirstName=first_name,
                LastName=last_name,
                Gender=gender,
                DateOfBirth=dob,
                ContactNumber=contact_number,
                EmergencyContact=emergency_contact,
                Address=address,
            )
            db.session.add(patient)
            db.session.flush()

            medical_record = MedicalRecord(
                PatientID=patient.PatientID,
                RecordDate=datetime.now(),
                Allergies=allergies,
                Conditions=conditions or diagnosis,
                Medications=medications,
                Notes=notes,
            )
            db.session.add(medical_record)

            bed.BedStatus = "Occupied"
            db.session.add(bed)

            admission = Admission(
                PatientID=patient.PatientID,
                BedID=bed_id,
                AdmissionDate=datetime.now(),
                Diagnosis=diagnosis,
                DoctorID=doctor_id,
            )
            db.session.add(admission)
            db.session.commit()

            audit_logger.log_audit(
                "patient",
                patient.PatientID,
                "create",
                {
                    "patient_name": f"{patient.FirstName} {patient.LastName}",
                    "details": {
                        "bed_id": bed_id,
                        "ward_id": ward_id,
                        "doctor_id": doctor_id,
                        "diagnosis": diagnosis,
                    },
                },
            )

            flash(
                f"{patient.FirstName} {patient.LastName} admitted successfully!",
                "success",
            )
            return redirect(url_for("main.admission"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error admitting patient: {str(e)}", "danger")

    return render_template("admission.html", doctors=doctors, wards=wards, form_data={})


@main_bp.route("/wards")
@login_required
@permission_required("view_patients")
def wards():
    return render_template("wards.html", user=current_user)


@main_bp.route("/patients")
@login_required
@permission_required("view_patients")
def patients():
    return render_template("patients.html", user=current_user)


@main_bp.route("/search-patients")
@login_required
@permission_required("view_patients")
def search_patients():
    search_term = request.args.get("query", "").strip()

    if search_term:

        search_words = search_term.split()

        filters = []
        for word in search_words:
            word_filter = or_(
                Patient.FirstName.ilike(f"%{word}%"),
                Patient.LastName.ilike(f"%{word}%"),
            )
            filters.append(word_filter)

        patients = (
            Patient.query.filter(and_(*filters)).order_by(Patient.LastName.asc()).all()
        )
    else:

        patients = Patient.query.order_by(Patient.LastName.asc()).all()

    patients_data = []
    for patient in patients:
        patients_data.append(
            {
                "patient_id": patient.PatientID,
                "patient_name": f"{patient.FirstName} {patient.LastName}",
                "gender": patient.Gender,
                "dob": patient.DateOfBirth.strftime("%Y-%m-%d")
                if patient.DateOfBirth
                else "",
                "contact": patient.ContactNumber,
                "emergency_contact": patient.EmergencyContact,
                "address": patient.Address,
            }
        )

    return jsonify(patients_data)


@main_bp.route("/get-patient/<int:patient_id>")
@login_required
@permission_required("view_patients")
def get_patient(patient_id):
    patient = Patient.query.get(patient_id)

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    return jsonify(
        {
            "patient_id": patient.PatientID,
            "first_name": patient.FirstName,
            "last_name": patient.LastName,
            "gender": patient.Gender,
            "dob": patient.DateOfBirth.strftime("%Y-%m-%d")
            if patient.DateOfBirth
            else "",
            "contact": patient.ContactNumber,
            "emergency_contact": patient.EmergencyContact,
            "address": patient.Address,
        }
    )


@main_bp.route("/update-patient/<int:patient_id>", methods=["POST"])
@login_required
@permission_required("view_patients")
def update_patient(patient_id):
    patient = Patient.query.get(patient_id)

    if not patient:
        return jsonify({"error": "Patient not found"}), 404

    data = request.json

    try:

        old_data = {
            "first_name": patient.FirstName,
            "last_name": patient.LastName,
            "gender": patient.Gender,
            "dob": patient.DateOfBirth.strftime("%Y-%m-%d")
            if patient.DateOfBirth
            else None,
            "contact": patient.ContactNumber,
            "emergency_contact": patient.EmergencyContact,
            "address": patient.Address,
        }

        patient.FirstName = data.get("first_name")
        patient.LastName = data.get("last_name")
        patient.Gender = data.get("gender")
        patient.DateOfBirth = (
            datetime.strptime(data.get("dob"), "%Y-%m-%d") if data.get("dob") else None
        )
        patient.ContactNumber = data.get("contact")
        patient.EmergencyContact = data.get("emergency_contact")
        patient.Address = data.get("address")

        new_data = {
            "first_name": patient.FirstName,
            "last_name": patient.LastName,
            "gender": patient.Gender,
            "dob": patient.DateOfBirth.strftime("%Y-%m-%d")
            if patient.DateOfBirth
            else None,
            "contact": patient.ContactNumber,
            "emergency_contact": patient.EmergencyContact,
            "address": patient.Address,
        }

        changes = {}
        for key in old_data:
            if str(old_data[key]) != str(new_data[key]):
                changes[key] = {"old": old_data[key], "new": new_data[key]}

        db.session.commit()

        current_app.log_audit(
            "patient",
            patient_id,
            "update",
            {
                "changes": changes,
                "patient_name": f"{patient.FirstName} {patient.LastName}",
            },
        )

        return jsonify(
            {"success": True, "message": "Patient information updated successfully"}
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@main_bp.route('/delete-patient/<int:patient_id>', methods=['POST'])
@login_required
def delete_patient(patient_id):
    
    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({'error': 'Unauthorized access. Only administrators can delete patients.'}), 403
    
    try:
        
        patient = Patient.query.get(patient_id)
        
        if not patient:
            return jsonify({'error': 'Patient not found'}), 404
        
        patient_name = f"{patient.FirstName} {patient.LastName}"
        
        active_admission = Admission.query.filter_by(
            PatientID=patient_id, 
            DischargeDate=None
        ).first()
        
        if active_admission:
            return jsonify({
                'error': 'Cannot delete patient with active admission. Please discharge the patient first.'
            }), 400
        
        admissions = Admission.query.filter_by(PatientID=patient_id).all()
        medical_records = MedicalRecord.query.filter_by(PatientID=patient_id).all()
           
        for record in medical_records:
            db.session.delete(record)
        
        for admission in admissions:
            db.session.delete(admission)
        
        db.session.delete(patient)
        db.session.commit()
        
        audit_logger.log_audit('patient', patient_id, 'delete', {
            'patient_name': patient_name,
            'details': f"Patient and all related records deleted by administrator {current_user.username}"
        })
        
        return jsonify({
            'success': True,
            'message': f'Patient {patient_name} has been deleted successfully.'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
@main_bp.route("/discharge-patient/<int:patient_id>", methods=["POST"])
@login_required
@permission_required("discharge_patient")
def discharge_patient(patient_id):
    try:

        patient = Patient.query.get(patient_id)
        if not patient:
            return jsonify({"error": "Patient not found"}), 404

        active_admission = Admission.query.filter_by(
            PatientID=patient_id, DischargeDate=None
        ).first()

        if active_admission:

            bed_id = active_admission.BedID

            active_admission.DischargeDate = datetime.now()

            bed = Bed.query.get(bed_id)
            if bed:
                bed.BedStatus = "Vacant"

            message = "Patient discharged successfully"

            audit_logger.log_audit(
                "admission",
                active_admission.AdmissionID,
                "discharge",
                {
                    "patient_id": patient_id,
                    "patient_name": f"{patient.FirstName} {patient.LastName}",
                    "bed_id": bed_id,
                    "admission_date": active_admission.AdmissionDate.strftime(
                        "%Y-%m-%d"
                    )
                    if active_admission.AdmissionDate
                    else None,
                    "discharge_date": datetime.now().strftime("%Y-%m-%d"),
                },
            )
        else:

            message = "Patient record updated (no active admission found)"

            audit_logger.log_audit(
                "patient",
                patient_id,
                "update",
                {
                    "patient_name": f"{patient.FirstName} {patient.LastName}",
                    "note": "Attempted discharge but no active admission found",
                },
            )

        db.session.commit()

        return jsonify({"success": True, "message": message})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route("/medical-records")
@login_required
@permission_required("view_medical_records")
def medical_records():

    patient_id = request.args.get("patient")

    query = db.session.query(MedicalRecord, Patient).join(
        Patient, MedicalRecord.PatientID == Patient.PatientID
    )

    if patient_id:
        query = query.filter(Patient.PatientID == patient_id)

    records = query.order_by(MedicalRecord.RecordDate.desc()).all()

    return render_template(
        "medical_records.html",
        records=records,
        user=current_user,
        patient_filter=patient_id,
    )


@main_bp.route("/search-records")
@login_required
@permission_required("view_medical_records")
def search_records():
    search_term = request.args.get("query", "").strip()
    patient_id = request.args.get("patient")

    query = db.session.query(MedicalRecord, Patient).join(
        Patient, MedicalRecord.PatientID == Patient.PatientID
    )

    if patient_id:

        query = query.filter(Patient.PatientID == patient_id)
    elif search_term:

        search_words = search_term.split()

        filters = []
        for word in search_words:
            word_filter = or_(
                Patient.FirstName.ilike(f"%{word}%"),
                Patient.LastName.ilike(f"%{word}%"),
            )
            filters.append(word_filter)

        query = query.filter(and_(*filters))

    records = query.order_by(MedicalRecord.RecordDate.desc()).all()

    records_data = []
    for record, patient in records:
        records_data.append(
            {
                "record_id": record.RecordID,
                "patient_id": patient.PatientID,
                "patient_name": f"{patient.FirstName} {patient.LastName}",
                "record_date": record.RecordDate.strftime("%Y-%m-%d")
                if record.RecordDate
                else "",
                "conditions": record.Conditions,
                "allergies": record.Allergies,
                "medications": record.Medications,
                "notes": record.Notes,
            }
        )

    return jsonify(records_data)


@main_bp.route("/get-record/<int:record_id>")
@login_required
@permission_required("view_medical_records")
def get_record(record_id):
    record = (
        db.session.query(MedicalRecord, Patient)
        .join(Patient, MedicalRecord.PatientID == Patient.PatientID)
        .filter(MedicalRecord.RecordID == record_id)
        .first()
    )

    if not record:
        return jsonify({"error": "Record not found"}), 404

    record_obj, patient = record

    return jsonify(
        {
            "record_id": record_obj.RecordID,
            "patient_id": patient.PatientID,
            "patient_name": f"{patient.FirstName} {patient.LastName}",
            "record_date": record_obj.RecordDate.strftime("%Y-%m-%d")
            if record_obj.RecordDate
            else "",
            "conditions": record_obj.Conditions,
            "allergies": record_obj.Allergies,
            "medications": record_obj.Medications,
            "notes": record_obj.Notes,
        }
    )


@main_bp.route("/get-record-with-admission/<int:record_id>")
@login_required
@permission_required("view_medical_records")
def get_record_with_admission(record_id):

    record = (
        db.session.query(MedicalRecord, Patient)
        .join(Patient, MedicalRecord.PatientID == Patient.PatientID)
        .filter(MedicalRecord.RecordID == record_id)
        .first()
    )

    if not record:
        return jsonify({"error": "Record not found"}), 404

    record_obj, patient = record

    admissions = (
        Admission.query.filter_by(PatientID=patient.PatientID)
        .order_by(Admission.AdmissionDate.desc())
        .all()
    )

    admission_data = []
    for admission in admissions:
        doctor = User.query.get(admission.DoctorID) if admission.DoctorID else None

        admission_data.append(
            {
                "admission_id": admission.AdmissionID,
                "admission_date": admission.AdmissionDate.strftime("%Y-%m-%d")
                if admission.AdmissionDate
                else "",
                "discharge_date": admission.DischargeDate.strftime("%Y-%m-%d")
                if admission.DischargeDate
                else "Not discharged",
                "diagnosis": admission.Diagnosis or "",
                "doctor": doctor.username if doctor else "Unknown",
                "bed_id": admission.BedID,
                "status": "Discharged" if admission.DischargeDate else "Active",
            }
        )

    return jsonify(
        {
            "record_id": record_obj.RecordID,
            "patient_id": patient.PatientID,
            "patient_name": f"{patient.FirstName} {patient.LastName}",
            "record_date": record_obj.RecordDate.strftime("%Y-%m-%d")
            if record_obj.RecordDate
            else "",
            "conditions": record_obj.Conditions,
            "allergies": record_obj.Allergies,
            "medications": record_obj.Medications,
            "notes": record_obj.Notes,
            "admissions": admission_data,
            "can_update": check_permission("update_medical_records"),
        }
    )


@main_bp.route("/update-record/<int:record_id>", methods=["POST"])
@login_required
@permission_required("update_medical_records")
def update_record(record_id):
    record = MedicalRecord.query.get(record_id)

    if not record:
        return jsonify({"error": "Record not found"}), 404

    data = request.json

    try:

        old_data = {
            "record_date": record.RecordDate.strftime("%Y-%m-%d")
            if record.RecordDate
            else None,
            "allergies": record.Allergies,
            "conditions": record.Conditions,
            "medications": record.Medications,
            "notes": record.Notes,
        }

        record.RecordDate = (
            datetime.strptime(data.get("record_date"), "%Y-%m-%d")
            if data.get("record_date")
            else None
        )
        record.Allergies = data.get("allergies")
        record.Conditions = data.get("conditions")
        record.Medications = data.get("medications")
        record.Notes = data.get("notes")

        patient = Patient.query.get(record.PatientID)
        patient_name = (
            f"{patient.FirstName} {patient.LastName}"
            if patient
            else f"ID: {record.PatientID}"
        )

        new_data = {
            "record_date": record.RecordDate.strftime("%Y-%m-%d")
            if record.RecordDate
            else None,
            "allergies": record.Allergies,
            "conditions": record.Conditions,
            "medications": record.Medications,
            "notes": record.Notes,
        }

        changes = {}
        for key in old_data:
            if str(old_data[key]) != str(new_data[key]):
                changes[key] = {"old": old_data[key], "new": new_data[key]}

        db.session.commit()

        audit_logger.log_audit(
            "medical_record",
            record_id,
            "update",
            {
                "patient_id": record.PatientID,
                "patient_name": patient_name,
                "changes": changes,
            },
        )

        return jsonify({"success": True, "message": "Record updated successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route("/admin")
@login_required
def admin_page():
    if not current_user.role_id or current_user.role_id != 1:
        flash(
            "Access denied. You must be an administrator to view this page.", "danger"
        )
        return redirect(url_for("main.dashboard"))

    return render_template("admin.html", user=current_user)


@main_bp.route("/get-wards")
@permission_required("view_patients")
@login_required
def get_wards():
    try:
        wards = Ward.query.order_by(Ward.WardName.asc()).all()

        wards_data = []
        for ward in wards:
            total_beds = len(ward.beds)
            occupied_beds = sum(1 for bed in ward.beds if bed.BedStatus == "Occupied")
            vacant_beds = sum(1 for bed in ward.beds if bed.BedStatus == "Vacant")

            wards_data.append(
                {
                    "ward_id": ward.WardID,
                    "ward_name": ward.WardName,
                    "ward_type": ward.WardType,
                    "ward_capacity": ward.WardCapacity,
                    "total_beds": total_beds,
                    "occupied_beds": occupied_beds,
                    "vacant_beds": vacant_beds,
                }
            )

        return jsonify(wards_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/search-wards")
@permission_required("view_patients")
@login_required
def search_wards():
    search_term = request.args.get("query", "").strip()

    try:
        if search_term:

            search_words = search_term.split()

            filters = []
            for word in search_words:
                filters.append(Ward.WardName.ilike(f"%{word}%"))

            wards = (
                Ward.query.filter(and_(*filters)).order_by(Ward.WardName.asc()).all()
            )
        else:
            wards = Ward.query.order_by(Ward.WardName.asc()).all()

        wards_data = []
        for ward in wards:
            total_beds = len(ward.beds)
            occupied_beds = sum(1 for bed in ward.beds if bed.BedStatus == "Occupied")
            vacant_beds = sum(1 for bed in ward.beds if bed.BedStatus == "Vacant")

            wards_data.append(
                {
                    "ward_id": ward.WardID,
                    "ward_name": ward.WardName,
                    "ward_type": ward.WardType,
                    "ward_capacity": ward.WardCapacity,
                    "total_beds": total_beds,
                    "occupied_beds": occupied_beds,
                    "vacant_beds": vacant_beds,
                }
            )

        return jsonify(wards_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/get-ward-beds/<int:ward_id>")
@login_required
def get_ward_beds(ward_id):
    try:
        beds = Bed.query.filter_by(WardID=ward_id).order_by(Bed.BedNumber.asc()).all()

        beds_data = []
        for bed in beds:

            patient_name = None
            if bed.BedStatus == "Occupied":

                admission = Admission.query.filter_by(
                    BedID=bed.BedID, DischargeDate=None
                ).first()

                if admission:
                    patient = Patient.query.get(admission.PatientID)
                    if patient:
                        patient_name = f"{patient.FirstName} {patient.LastName}"

            beds_data.append(
                {
                    "bed_id": bed.BedID,
                    "bed_number": bed.BedNumber,
                    "bed_status": bed.BedStatus,
                    "patient_name": patient_name,
                }
            )

        return jsonify(beds_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/get-bed/<int:bed_id>")
@login_required
def get_bed(bed_id):
    try:
        bed = Bed.query.get(bed_id)

        if not bed:
            return jsonify({"error": "Bed not found"}), 404

        bed_data = {
            "bed_id": bed.BedID,
            "ward_id": bed.WardID,
            "bed_number": bed.BedNumber,
            "bed_status": bed.BedStatus,
            "patient_info": None,
        }

        if bed.BedStatus == "Occupied":

            admission = Admission.query.filter_by(
                BedID=bed.BedID, DischargeDate=None
            ).first()

            if admission:
                patient = Patient.query.get(admission.PatientID)
                doctor = (
                    User.query.get(admission.DoctorID) if admission.DoctorID else None
                )

                if patient:
                    bed_data["patient_info"] = {
                        "patient_id": patient.PatientID,
                        "name": f"{patient.FirstName} {patient.LastName}",
                        "admission_date": admission.AdmissionDate.strftime("%Y-%m-%d"),
                        "doctor": doctor.username if doctor else "Unknown",
                        "diagnosis": admission.Diagnosis,
                    }

        return jsonify(bed_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/update-bed/<int:bed_id>", methods=["POST"])
@login_required
def update_bed(bed_id):
    try:
        bed = Bed.query.get(bed_id)

        if not bed:
            return jsonify({"error": "Bed not found"}), 404

        data = request.json
        previous_status = bed.BedStatus
        new_status = data.get("bed_status")

        bed.BedStatus = new_status

        if previous_status == "Occupied" and new_status != "Occupied":

            admission = Admission.query.filter_by(
                BedID=bed.BedID, DischargeDate=None
            ).first()

            if admission:

                admission.DischargeDate = datetime.now()

                patient = Patient.query.get(admission.PatientID)
                patient_name = (
                    f"{patient.FirstName} {patient.LastName}"
                    if patient
                    else f"ID: {admission.PatientID}"
                )

                audit_logger.log_audit(
                    "admission",
                    admission.AdmissionID,
                    "discharge",
                    {
                        "patient_id": admission.PatientID,
                        "patient_name": patient_name,
                        "bed_id": bed_id,
                        "note": "Discharged due to bed status change",
                    },
                )

        db.session.commit()

        ward = Ward.query.get(bed.WardID)
        ward_name = ward.WardName if ward else f"ID: {bed.WardID}"

        audit_logger.log_audit(
            "bed",
            bed_id,
            "update",
            {
                "bed_number": bed.BedNumber,
                "ward_id": bed.WardID,
                "ward_name": ward_name,
                "changes": {"status": {"old": previous_status, "new": new_status}},
            },
        )

        return jsonify(
            {
                "success": True,
                "message": "Bed updated successfully",
                "previous_status": previous_status,
                "new_status": new_status,
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route("/get-ward/<int:ward_id>")
@login_required
def get_ward(ward_id):

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        ward = Ward.query.get(ward_id)

        if not ward:
            return jsonify({"error": "Ward not found"}), 404

        return jsonify(
            {
                "ward_id": ward.WardID,
                "ward_name": ward.WardName,
                "ward_type": ward.WardType,
                "ward_capacity": ward.WardCapacity,
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/create-ward", methods=["POST"])
@login_required
def create_ward():

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        data = request.json

        ward = Ward(
            WardName=data.get("ward_name"),
            WardType=data.get("ward_type"),
            WardCapacity=data.get("ward_capacity"),
        )

        db.session.add(ward)
        db.session.commit()

        audit_logger.log_audit(
            "ward",
            ward.WardID,
            "create",
            {
                "ward_name": ward.WardName,
                "ward_type": ward.WardType,
                "ward_capacity": ward.WardCapacity,
            },
        )

        return jsonify(
            {
                "success": True,
                "message": "Ward created successfully",
                "ward_id": ward.WardID,
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route("/update-ward/<int:ward_id>", methods=["POST"])
@login_required
def update_ward(ward_id):

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        ward = Ward.query.get(ward_id)

        if not ward:
            return jsonify({"error": "Ward not found"}), 404

        data = request.json

        old_data = {
            "ward_name": ward.WardName,
            "ward_type": ward.WardType,
            "ward_capacity": ward.WardCapacity,
        }

        ward.WardName = data.get("ward_name")
        ward.WardType = data.get("ward_type")
        ward.WardCapacity = data.get("ward_capacity")

        new_data = {
            "ward_name": ward.WardName,
            "ward_type": ward.WardType,
            "ward_capacity": ward.WardCapacity,
        }

        changes = {}
        for key in old_data:
            if str(old_data[key]) != str(new_data[key]):
                changes[key] = {"old": old_data[key], "new": new_data[key]}

        db.session.commit()

        audit_logger.log_audit(
            "ward", ward_id, "update", {"ward_name": ward.WardName, "changes": changes}
        )

        return jsonify({"success": True, "message": "Ward updated successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route("/delete-ward/<int:ward_id>", methods=["POST"])
@login_required
def delete_ward(ward_id):

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        ward = Ward.query.get(ward_id)

        if not ward:
            return jsonify({"error": "Ward not found"}), 404

        ward_name = ward.WardName

        occupied_beds = Bed.query.filter_by(
            WardID=ward_id, BedStatus="Occupied"
        ).count()

        if occupied_beds > 0:
            return (
                jsonify(
                    {
                        "error": f"Cannot delete ward: {occupied_beds} bed(s) are currently occupied"
                    }
                ),
                400,
            )

        Bed.query.filter_by(WardID=ward_id).delete()

        db.session.delete(ward)
        db.session.commit()

        audit_logger.log_audit("ward", ward_id, "delete", {"ward_name": ward_name})

        return jsonify({"success": True, "message": "Ward deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route("/create-bed", methods=["POST"])
@login_required
def create_bed():

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        data = request.json

        existing_bed = Bed.query.filter_by(
            WardID=data.get("ward_id"), BedNumber=data.get("bed_number")
        ).first()

        if existing_bed:
            return (
                jsonify(
                    {
                        "error": f'Bed number {data.get("bed_number")} already exists in this ward'
                    }
                ),
                400,
            )

        bed = Bed(
            WardID=data.get("ward_id"),
            BedNumber=data.get("bed_number"),
            BedStatus=data.get("bed_status", "Vacant"),
        )

        db.session.add(bed)
        db.session.commit()

        return jsonify(
            {"success": True, "message": "Bed added successfully", "bed_id": bed.BedID}
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route("/delete-bed/<int:bed_id>", methods=["POST"])
@login_required
def delete_bed(bed_id):

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        bed = Bed.query.get(bed_id)

        if not bed:
            return jsonify({"error": "Bed not found"}), 404

        if bed.BedStatus == "Occupied":
            return (
                jsonify(
                    {
                        "error": "Cannot delete an occupied bed. Please discharge the patient first."
                    }
                ),
                400,
            )

        has_admissions = Admission.query.filter_by(BedID=bed_id).count() > 0

        if has_admissions:
            return (
                jsonify(
                    {
                        "error": "Cannot delete bed with admission history. Consider marking it as out of service instead."
                    }
                ),
                400,
            )

        db.session.delete(bed)
        db.session.commit()

        return jsonify({"success": True, "message": "Bed deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route("/users")
@login_required
def users():

    if not current_user.role_id or current_user.role_id != 1:
        flash(
            "Access denied. You must be an administrator to view this page.", "danger"
        )
        return redirect(url_for("main.dashboard"))

    return render_template("users.html", user=current_user)


@main_bp.route("/search-users")
@login_required
def search_users():

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    search_term = request.args.get("query", "").strip()

    if search_term:

        search_words = search_term.split()

        filters = []
        for word in search_words:
            filters.append(User.username.ilike(f"%{word}%"))

        users = User.query.filter(and_(*filters)).order_by(User.username.asc()).all()
    else:

        users = User.query.order_by(User.username.asc()).all()

    users_data = []
    for user in users:
        role_name = user.role.role_name if user.role else "No Role"
        users_data.append(
            {
                "user_id": user.id,
                "username": user.username,
                "role_id": user.role_id,
                "role_name": role_name,
            }
        )

    return jsonify(users_data)


@main_bp.route("/get-user/<int:user_id>")
@login_required
def get_user(user_id):

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    role_name = user.role.role_name if user.role else "No Role"

    return jsonify(
        {
            "user_id": user.id,
            "username": user.username,
            "role_id": user.role_id,
            "role_name": role_name,
        }
    )


@main_bp.route("/update-user/<int:user_id>", methods=["POST"])
@login_required
def update_user(user_id):

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.json

    try:

        old_username = user.username
        old_role_id = user.role_id

        user.username = data.get("username")
        user.role_id = data.get("role_id")

        password_changed = False
        if data.get("password"):
            from werkzeug.security import generate_password_hash

            user.password = generate_password_hash(data.get("password"))
            password_changed = True

        old_role = Role.query.get(old_role_id)
        old_role_name = old_role.role_name if old_role else f"ID: {old_role_id}"

        new_role = Role.query.get(user.role_id)
        new_role_name = new_role.role_name if new_role else f"ID: {user.role_id}"

        db.session.commit()

        changes = {}
        if old_username != user.username:
            changes["username"] = {"old": old_username, "new": user.username}

        if old_role_id != user.role_id:
            changes["role"] = {"old": old_role_name, "new": new_role_name}

        if password_changed:
            changes["password"] = {
                "old": "[Password was changed]",
                "new": f'Changed by {current_user.username} on {datetime.now().strftime("%Y-%m-%d at %H:%M")}',
            }

        audit_logger.log_audit(
            "user", user_id, "update", {"user_name": user.username, "changes": changes}
        )

        return jsonify(
            {"success": True, "message": "User information updated successfully"}
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route("/create-user", methods=["POST"])
@login_required
def create_user():

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    data = request.json

    try:

        existing_user = User.query.filter_by(username=data.get("username")).first()
        if existing_user:
            return jsonify({"error": "Username already exists"}), 400

        from werkzeug.security import generate_password_hash

        hashed_password = generate_password_hash(data.get("password"))

        new_user = User(
            username=data.get("username"),
            password=hashed_password,
            role_id=data.get("role_id"),
        )

        db.session.add(new_user)
        db.session.commit()

        role = Role.query.get(data.get("role_id"))
        role_name = role.role_name if role else f"ID: {data.get('role_id')}"

        audit_logger.log_audit(
            "user",
            new_user.id,
            "create",
            {
                "user_name": new_user.username,
                "role_id": new_user.role_id,
                "role_name": role_name,
            },
        )

        return jsonify(
            {
                "success": True,
                "message": "User created successfully",
                "user_id": new_user.id,
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route("/get-roles")
@login_required
def get_roles():

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    try:
        roles = Role.query.order_by(Role.role_name).all()
        roles_data = [
            {"role_id": role.id, "role_name": role.role_name} for role in roles
        ]
        return jsonify(roles_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@main_bp.route("/delete-user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    if user_id == current_user.id:
        return jsonify({"error": "You cannot delete your own account"}), 400

    try:
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        username = user.username

        db.session.delete(user)
        db.session.commit()

        audit_logger.log_audit("user", user_id, "delete", {"user_name": username})

        return jsonify({"success": True, "message": "User deleted successfully"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@main_bp.route("/audit-logs")
@login_required
def audit_logs():

    if not current_user.role_id or current_user.role_id != 1:
        flash(
            "Access denied. You must be an administrator to view this page.", "danger"
        )
        return redirect(url_for("main.dashboard"))

    return render_template("audit_logs.html", user=current_user)


@main_bp.route("/search-audit-logs")
@login_required
def search_audit_logs():

    if not current_user.role_id or current_user.role_id != 1:
        return jsonify({"error": "Unauthorized access"}), 403

    entity_type = request.args.get("entity_type", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    user_id = request.args.get("user_id", "")

    try:

        logs = audit_logger.get_logs(
            entity_type=entity_type,
            date_from=date_from,
            date_to=date_to,
            user_id=user_id,
        )

        return jsonify(logs)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

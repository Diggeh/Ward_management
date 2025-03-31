from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from database import db
from models import Admission, Ward, Patient 
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

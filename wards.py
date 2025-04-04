from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database import db  # Import db from database.py
from models import Ward, Bed

wards_bp = Blueprint('wards', __name__)

@wards_bp.route('/', methods=['POST'])
@login_required
def create_ward():
    if current_user.Role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    data = request.get_json()
    new_ward = Ward(
        WardName=data['WardName'],
        WardCapacity=data.get('WardCapacity'),
        WardType=data['WardType']
    )
    db.session.add(new_ward)
    db.session.commit()
    return jsonify({'message': 'Ward created successfully'}), 201

@wards_bp.route('/', methods=['GET'])
@login_required
def list_wards():
    wards = Ward.query.all()
    result = [{
        'WardID': w.WardID,
        'WardName': w.WardName,
        'WardCapacity': w.WardCapacity,
        'WardType': w.WardType,
        'Beds': [{'BedID': b.BedID, 'BedNumber': b.BedNumber, 'BedStatus': b.BedStatus} 
                 for b in Bed.query.filter_by(WardID=w.WardID).all()]
    } for w in wards]
    return jsonify(result), 200
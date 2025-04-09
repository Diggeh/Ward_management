from database import db
from flask_login import UserMixin
from sqlalchemy import CheckConstraint

class Admission(db.Model):
    __tablename__ = "Admissions"
    AdmissionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PatientID = db.Column(
        db.Integer, db.ForeignKey("Patients.PatientID"), nullable=False
    )
    BedID = db.Column(db.Integer, db.ForeignKey("Beds.BedID"), nullable=False)
    DoctorID = db.Column(
        db.Integer, db.ForeignKey("users.id")
    )  
    AdmissionDate = db.Column(db.Date, nullable=False)
    DischargeDate = db.Column(db.Date)
    Diagnosis = db.Column(db.Text)
    

    
    patient = db.relationship("Patient", backref="admissions")
    bed = db.relationship("Bed", backref="admissions")
    doctor = db.relationship(
        "User", backref="doctor_admissions", foreign_keys=[DoctorID]
    )  


class Bed(db.Model):
    __tablename__ = "Beds"
    BedID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    WardID = db.Column(db.Integer, db.ForeignKey("Wards.WardID"), nullable=False)
    BedNumber = db.Column(db.Integer, nullable=False)
    BedStatus = db.Column(db.Text)

    
    ward = db.relationship("Ward", backref="beds")
    


class MedicalRecord(db.Model):
    __tablename__ = "MedicalRecords"
    RecordID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PatientID = db.Column(
        db.Integer, db.ForeignKey("Patients.PatientID"), nullable=False
    )
    RecordDate = db.Column(db.Date, nullable=False)
    Allergies = db.Column(db.Text)
    Conditions = db.Column(db.Text)
    Medications = db.Column(db.Text)
    Notes = db.Column(db.Text)

    
    patient = db.relationship("Patient", backref="medical_records")


class Patient(db.Model):
    __tablename__ = "Patients"
    PatientID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FirstName = db.Column(db.Text, nullable=False)
    LastName = db.Column(db.Text, nullable=False)
    DateOfBirth = db.Column(db.Date, nullable=False)
    Gender = db.Column(db.Text, CheckConstraint("Gender IN ('Male', 'Female', 'Other')"))
    ContactNumber = db.Column(db.Integer, CheckConstraint('ContactNumber >= 100000000 AND ContactNumber < 10000000000'))
    EmergencyContact = db.Column(db.Integer, CheckConstraint('EmergencyContact >= 100000000 AND EmergencyContact < 10000000000'))
    Address = db.Column(db.Text)

    


class Ward(db.Model):
    __tablename__ = "Wards"
    WardID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    WardName = db.Column(db.Text, nullable=False)
    WardCapacity = db.Column(db.Integer)
    WardType = db.Column(db.Text)

    


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_name = db.Column(db.Text, nullable=False, unique=True)
    users = db.relationship("User", backref="role")

    


class Permission(db.Model):
    __tablename__ = "permissions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    permission_name = db.Column(db.Text, nullable=False, unique=True)

    


class RolePermission(db.Model):
    __tablename__ = "role_permissions"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))
    permission_id = db.Column(db.Integer, db.ForeignKey("permissions.id"))

    
    role = db.relationship("Role", backref="permissions_assoc")
    permission = db.relationship("Permission", backref="roles_assoc")


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, nullable=False, unique=True)
    password = db.Column(db.Text, nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"))

    

    def get_id(self):
        return str(self.id)

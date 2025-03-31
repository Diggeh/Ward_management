from database import db  # Import db from database.py
from flask_login import UserMixin

class Admission(db.Model):
    __tablename__ = 'Admissions'
    AdmissionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PatientID = db.Column(db.Integer, db.ForeignKey('Patients.PatientID'), nullable=False)
    BedID = db.Column(db.Integer, db.ForeignKey('Beds.BedID'), nullable=False)
    AdmissionDate = db.Column(db.Date, nullable=False)
    DischargeDate = db.Column(db.Date, nullable=False)
    Diagnosis = db.Column(db.Text)
    DoctorInCharge = db.Column(db.Text)

class Bed(db.Model):
    __tablename__ = 'Beds'
    BedID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    WardID = db.Column(db.Integer, db.ForeignKey('Wards.WardID'), nullable=False)
    BedNumber = db.Column(db.Integer, nullable=False)
    BedStatus = db.Column(db.Text)

class Records(db.Model):
    __tablename__ = 'MedicalRecords'
    RecordID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    PatientID = db.Column(db.Integer, db.ForeignKey('Patients.PatientID'))
    RecordDate = db.Column(db.Date, nullable=False)
    Allergies = db.Column(db.Text)
    Conditions = db.Column(db.Text)
    Medications = db.Column(db.Text)
    Notes = db.Column(db.Text)

class Patient(db.Model):
    __tablename__ = 'Patients'
    PatientID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    FirstName = db.Column(db.Text, nullable=False)
    LastName = db.Column(db.Text, nullable=False)
    DateOfBirth = db.Column(db.Date, nullable=False)
    Gender = db.Column(db.Integer)
    ContactNumber = db.Column(db.Integer)
    EmergencyContact = db.Column(db.Integer)
    Address = db.Column(db.Text)

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Username = db.Column(db.Text, nullable=False, unique=True)
    Password = db.Column(db.Text, nullable=False)
    Role = db.Column(db.Text)
    FullName = db.Column(db.Text, nullable=False)
    ContactNumber = db.Column(db.Integer)

    def get_id(self):
        return str(self.UserID)

class Ward(db.Model):
    __tablename__ = 'Wards'
    WardID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    WardName = db.Column(db.Text, nullable=False)
    WardCapacity = db.Column(db.Integer)
    WardType = db.Column(db.Text)

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, TextAreaField, DateField
from wtforms.validators import DataRequired

class AdmissionForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    dob = DateField('Date of Birth', validators=[DataRequired()], format='%Y-%m-%d')
    gender = SelectField('Gender', choices=[
        ('', 'Select Gender'),
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    contact_number = StringField('Contact Number')
    emergency_contact = StringField('Emergency Contact')
    doctor = SelectField('Doctor in Charge', validators=[DataRequired()])
    address = TextAreaField('Address')
    ward = SelectField('Ward', coerce=int, validators=[DataRequired()])
    bed = SelectField('Bed Number', coerce=int, validators=[DataRequired()])
    diagnosis = TextAreaField('Diagnosis', validators=[DataRequired()])
    allergies = TextAreaField('Allergies')

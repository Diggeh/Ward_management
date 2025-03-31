from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'
DB_PATH = 'WardManagementDB.db'

# Database Helper
def query_db(query, args=(), one=False):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(query, args)
        rv = cur.fetchall()
        return (rv[0] if rv else None) if one else rv

# Routes
@app.route('/')
def home():
    if 'user' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user = query_db('SELECT * FROM users WHERE username = ? AND password = ?', (request.form['username'], request.form['password']), one=True)
    if user:
        session['user'] = user[1]
        session['role'] = user[3]
        return redirect(url_for('dashboard'))
    return 'Login Failed'

@app.route('/dashboard')
def dashboard():
    patients = query_db('SELECT * FROM patients')

    recent_admissions = query_db(
    '''
    SELECT * FROM admissions
    WHERE AdmissionDate >= datetime('now', '-7 days')
    ORDER BY AdmissionDate DESC
    '''
    )

    recent_discharges = query_db(
            '''
            SELECT * FROM admissions
            WHERE DischargeDate IS NOT NULL AND DischargeDate >= datetime('now', '-7 days')
            ORDER BY DischargeDate DESC
            '''
        )
    return render_template('dashboard.html',
    recent_admissions=recent_admissions,
    recent_discharges=recent_discharges
    )

@app.route('/admit', methods=['POST'])
def admit():
    name = request.form['name']
    ward = request.form['ward']
    bed = request.form['bed']
    status = 'Admitted'
    query_db('INSERT INTO patients (name, ward, bed, status) VALUES (?, ?, ?, ?)', (name, ward, bed, status))
    return redirect(url_for('dashboard'))

@app.route('/discharge/<int:patient_id>')
def discharge(patient_id):
    query_db('UPDATE patients SET status = ? WHERE id = ?', ('Discharged', patient_id))
    return redirect(url_for('dashboard'))

@app.route('/patient/<int:patient_id>')
def patient_details(patient_id):
    patient = query_db('SELECT * FROM patients WHERE id = ?', (patient_id,), one=True)
    return render_template('patient_details.html', patient=patient)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
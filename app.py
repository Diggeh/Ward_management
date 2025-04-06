from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from database import db
from auth import auth_bp
from wards import wards_bp
from main import main_bp
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
db_name = 'WardManagementDB.db'
db_path = os.path.join(basedir, db_name)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  
app.config['SECRET_KEY'] = 'd31a164b29bbdef3d4bb99fc832d5f2f95ba9f243ced9c43'
db.init_app(app)

if not os.path.exists(db_path):
    print(f"Error: Database file not found at {db_path}")
else:
    print(f"Connecting to database at {db_path}")
    
# Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login_page'
login_manager.login_message_category = 'info'

# Load User
@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.filter_by(id=int(user_id)).first()

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(wards_bp, url_prefix='/wards')
app.register_blueprint(main_bp)

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login_page'))

# Check tables
with app.app_context():
    from sqlalchemy import inspect
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")
        required_tables = ['users', 'Patients', 'Wards', 'Beds', 'Admissions', 'MedicalRecords']
        for table in required_tables:
             if table not in tables:
                 print(f"Warning: '{table}' table not found in the database.")
    except Exception as e:
        print(f"Error inspecting database: {e}")

if __name__ == '__main__':
    app.run(debug=True)
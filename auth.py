from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash 
from flask_login import login_user, logout_user, login_required, current_user 
from werkzeug.security import check_password_hash 
from database import db
from models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET'])
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard')) 
    return render_template('login.html') 

@auth_bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        flash('Username and password are required.', 'warning')
        return redirect(url_for('auth.login_page'))

    user = User.query.filter_by(Username=username).first()

    if user and check_password_hash(user.Password, password):
        login_user(user) 
        flash('Logged in successfully!', 'success')

        return redirect(url_for('main.dashboard'))
    else:
        flash('Invalid username or password.', 'danger')

        return redirect(url_for('auth.login_page'))

@auth_bp.route('/logout')
@login_required 
def logout():
    logout_user() 
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login_page')) 

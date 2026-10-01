"""
Local2Farm Authentication Routes
Handles farmer registration, login (farmer & admin), and session management.
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, Farmer, Admin

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def farmer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'farmer':
            flash("Farmer login required.", "warning")
            return redirect(url_for('auth.login', role='farmer'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash("Administrator login required.", "warning")
            return redirect(url_for('auth.login', role='admin'))
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Farmer Registration"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        mobile = request.form.get('mobile', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        location = request.form.get('location', '').strip()
        district = request.form.get('district', '').strip()
        state = request.form.get('state', '').strip()

        # Simple validations
        if not all([name, mobile, email, password, location, district, state]):
            flash("All fields are required. Please fill in all details.", "danger")
            return render_template('register.html', form_data=request.form)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html', form_data=request.form)

        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "danger")
            return render_template('register.html', form_data=request.form)

        # Check existing user
        if Farmer.query.filter_by(email=email).first():
            flash("A farmer with this email is already registered. Please login.", "warning")
            return redirect(url_for('auth.login', role='farmer'))

        # Create and save farmer
        new_farmer = Farmer(
            name=name,
            mobile=mobile,
            email=email,
            location=location,
            district=district,
            state=state
        )
        new_farmer.set_password(password)
        db.session.add(new_farmer)
        db.session.commit()

        flash("Registration successful! You can now log in with your credentials.", "success")
        return redirect(url_for('auth.login', role='farmer'))

    return render_template('register.html', form_data={})


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Unified Login for Farmer and Admin"""
    role = request.args.get('role', 'farmer')

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        role = request.form.get('role', 'farmer')

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template('login.html', active_role=role)

        if role == 'admin':
            admin = Admin.query.filter_by(email=email).first()
            if admin and admin.check_password(password):
                session.clear()
                session['user_id'] = admin.id
                session['user_role'] = 'admin'
                session['user_name'] = admin.name
                session['user_email'] = admin.email
                flash(f"Welcome back, Administrator {admin.name}!", "success")
                return redirect(url_for('admin.dashboard'))
            else:
                flash("Invalid administrator email or password.", "danger")
        else:
            farmer = Farmer.query.filter_by(email=email).first()
            if farmer and farmer.check_password(password):
                session.clear()
                session['user_id'] = farmer.id
                session['user_role'] = 'farmer'
                session['user_name'] = farmer.name
                session['user_email'] = farmer.email
                session['farmer_location'] = farmer.location
                flash(f"Welcome back, {farmer.name}!", "success")
                return redirect(url_for('farmer.dashboard'))
            else:
                flash("Invalid farmer email or password.", "danger")

    return render_template('login.html', active_role=role)


@auth_bp.route('/logout')
def logout():
    """Logout current user"""
    name = session.get('user_name', 'User')
    session.clear()
    flash(f"Goodbye, {name}. You have been logged out successfully.", "info")
    return redirect(url_for('home'))

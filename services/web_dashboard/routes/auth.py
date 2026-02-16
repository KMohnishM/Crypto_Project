from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from datetime import datetime, timedelta

from models.user import User, UserSession, db

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(username=username).first()
        
        # If user does not exist, redirect to registration
        if not user:
            flash('Account not found. Please register first.')
            return redirect(url_for('auth.register'))

        # If user exists but password is wrong, stay on login
        if not user.check_password(password):
            flash('Incorrect password. Please try again.')
            return redirect(url_for('auth.login'))
            
        # If user exists and is inactive
        if not user.is_active:
            flash('This account has been deactivated. Please contact an administrator.')
            return redirect(url_for('auth.login'))
            
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log in user (Flask-Login handles session management)
        login_user(user, remember=remember)
        
        # Redirect to the page the user was trying to access
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
            
        return redirect(next_page)
        
    return render_template('auth/login.html')
    
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        requested_role = request.form.get('requested_role', 'technician')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists.')
            return redirect(url_for('auth.register'))
            
        # Create new user - default role is 'technician' for security
        # Admins can later upgrade role based on requested_role
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='technician',  # Default lowest privilege role
            requested_role=requested_role  # Store what they requested
        )
        new_user.set_password(password)
        
        # Add and commit to database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')

@auth.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Update profile information
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.email = request.form.get('email')
        
        # Only update password if provided
        if request.form.get('password'):
            current_user.set_password(request.form.get('password'))
            
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/edit_profile.html')

# Admin routes for user management
@auth.route('/admin/users')
@login_required
def admin_users():
    if not current_user.has_permission('manage_users'):
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.dashboard'))
        
    users = User.query.all()
    return render_template('auth/admin_users.html', users=users)

@auth.route('/admin/users/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.has_permission('manage_users'):
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.dashboard'))
        
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.role = request.form.get('role')
        user.department = request.form.get('department')
        user.is_active = True if request.form.get('is_active') else False
        
        # Only update password if provided
        if request.form.get('password'):
            user.set_password(request.form.get('password'))
            
        db.session.commit()
        flash(f'User {user.username} has been updated.')
        return redirect(url_for('auth.admin_users'))
        
    return render_template('auth/admin_edit_user.html', user=user)

@auth.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
def admin_create_user():
    if not current_user.has_permission('manage_users'):
        flash('You do not have permission to access this page.')
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        role = request.form.get('role')
        department = request.form.get('department')
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('auth.admin_create_user'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already exists.')
            return redirect(url_for('auth.admin_create_user'))
            
        # Create new user
        new_user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=role,
            department=department,
            is_active=True
        )
        new_user.set_password(password)
        
        # Add and commit to database
        db.session.add(new_user)
        db.session.commit()
        
        flash(f'User {username} has been created.')
        return redirect(url_for('auth.admin_users'))
        
    return render_template('auth/admin_create_user.html')
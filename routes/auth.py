from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from models import User
from app import db
from utils.helpers import requires_role

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password) and user.is_active:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/users')
@login_required
@requires_role('Admin')
def users():
    users = User.query.all()
    return render_template('auth/users.html', users=users)

@auth_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
@requires_role('Admin')
def new_user():
    if request.method == 'POST':
        user = User(
            full_name=request.form['full_name'],
            username=request.form['username'],
            password_hash=generate_password_hash(request.form['password']),
            role=request.form['role'],
            is_active=True
        )
        db.session.add(user)
        db.session.commit()
        flash('User created successfully', 'success')
        return redirect(url_for('auth.users'))
    
    return render_template('auth/new_user.html')

@auth_bp.route('/users/<int:user_id>/toggle')
@login_required
@requires_role('Admin')
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'User {"activated" if user.is_active else "deactivated"} successfully', 'success')
    return redirect(url_for('auth.users'))

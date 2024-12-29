from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from forms import PasswordChangeForm
from models.base import db

bp = Blueprint('profile', __name__)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    password_form = PasswordChangeForm()
    
    if password_form.validate_on_submit():
        if check_password_hash(current_user.password_hash, password_form.current_password.data):
            current_user.password_hash = generate_password_hash(password_form.new_password.data)
            db.session.commit()
            flash('Password updated successfully!', 'success')
            return redirect(url_for('profile.profile'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    # Choose template based on user role
    if current_user.is_admin() or current_user.is_staff():
        template = 'profile/admin_staff_profile.html'
    elif current_user.is_teacher():
        template = 'profile/teacher_profile.html'
    elif current_user.is_observer():
        template = 'profile/observer_profile.html'
    else:  # student
        template = 'profile/student_profile.html'
    
    return render_template(template, password_form=password_form) 
from flask import render_template
from flask_login import login_required, current_user
from functools import wraps
from .base import create_blueprint

bp = create_blueprint('admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_admin() or current_user.is_staff()):
            return render_template('errors/403.html'), 403
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html') 
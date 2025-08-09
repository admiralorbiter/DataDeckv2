from flask import flash, redirect, render_template, url_for
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash

from forms import LoginForm
from models import User

from .base import create_blueprint

bp = create_blueprint("auth")


# Named endpoint resolves as 'auth.login' for Flask-Login redirect
@bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # Primary: treat form value as email; Fallback: username for backwards comp
        value = form.username.data
        user = User.query.filter_by(email=value).first()
        if not user:
            user = User.query.filter_by(username=value).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("Logged in successfully.", "success")
            # Redirect by role: admins/staff to admin dashboard; others to home
            if user.is_admin() or user.is_staff():
                return redirect(url_for("admin.admin_dashboard"))
            return redirect(url_for("main.index"))
        else:
            flash("Invalid username or password.", "danger")
    return render_template("login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user
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
        # Primary: treat form value as email; Fallback: username
        value = form.username.data
        user = User.query.filter_by(email=value).first()
        if not user:
            user = User.query.filter_by(username=value).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            # All users now use Flask-Login (unified authentication)
            login_user(user)
            flash("Logged in successfully.", "success")

            # Role-based redirect after login
            if user.is_observer():
                return redirect(url_for("main.observer_dashboard"))
            elif user.is_admin() or user.is_staff():
                return redirect(url_for("admin.admin_dashboard"))
            else:
                return redirect(url_for("main.index"))
        else:
            flash("Invalid username or password.", "danger")
    return render_template("login.html", form=form)


@bp.route("/logout")
def logout():
    # All users now use Flask-Login (unified authentication)
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("main.index"))

    # No user logged in → redirect to login
    return redirect(url_for("auth.login"))

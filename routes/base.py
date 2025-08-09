from functools import wraps

from flask import Blueprint, flash, redirect, session, url_for
from flask_login import current_user


def create_blueprint(name):
    """Create a blueprint with the given name"""
    return Blueprint(name, __name__)


def observer_required(f):
    """Decorator to require an active observer session (not Flask-Login)."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("observer_id"):
            flash("Observer login required.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


def student_required(f):
    """Decorator to require a student session (e.g., set by PIN login)."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("student_id"):
            flash("Student access required.", "warning")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated_function


def teacher_or_student_required(f):
    """Decorator to require either teacher login or student session."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is logged in as teacher/admin
        if current_user.is_authenticated:
            return f(*args, **kwargs)

        # Check if student is logged in via session
        if session.get("student_id"):
            return f(*args, **kwargs)

        # Neither teacher nor student is logged in
        flash("Please log in to access this page.", "warning")
        return redirect(url_for("main.index"))

    return decorated_function

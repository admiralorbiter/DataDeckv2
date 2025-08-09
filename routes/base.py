from functools import wraps

from flask import Blueprint, flash, redirect, session, url_for


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

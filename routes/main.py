from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from models import District, School, User, db

from .base import create_blueprint, student_required

bp = create_blueprint("main")


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/observer/dashboard")
@login_required
def observer_dashboard():
    # Check if current user is an observer
    if not current_user.is_observer():
        flash("Access denied. Observer role required.", "danger")
        return redirect(url_for("main.index"))

    # Current user is the observer (no need to query separately)
    observer = current_user

    district = None
    schools = []
    if observer.district_id:
        district = db.session.get(District, observer.district_id)
        if district:
            schools = (
                School.query.filter_by(district_id=district.id)
                .order_by(School.name)
                .all()
            )

    return render_template(
        "observer/dashboard.html",
        observer=observer,
        district=district,
        schools=schools,
    )


@bp.route("/observer/schools/<int:school_id>")
@login_required
def observer_school(school_id: int):
    # Check if current user is an observer
    if not current_user.is_observer():
        flash("Access denied. Observer role required.", "danger")
        return redirect(url_for("main.index"))

    # Current user is the observer
    observer = current_user

    school = db.session.get(School, school_id)
    if (
        not school
        or not observer.district_id
        or school.district_id != observer.district_id
    ):
        # Forbidden: school not in observer's district
        return render_template("errors/403.html"), 403

    teachers = (
        User.query.filter(
            User.role == User.Role.TEACHER,
            User.school_id == school.id,
        )
        .order_by(User.last_name, User.first_name)
        .all()
    )

    return render_template(
        "observer/school_detail.html",
        observer=observer,
        district_id=observer.district_id,
        school=school,
        teachers=teachers,
    )


@bp.route("/student/protected")
@student_required
def student_protected():
    # Simple protected endpoint used for future tests
    return {"ok": True}

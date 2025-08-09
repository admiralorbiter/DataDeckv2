from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash

from forms import StudentLoginForm
from models import User, db
from models.district import District
from models.school import School
from models.student import Student

from .base import create_blueprint, student_required

bp = create_blueprint("main")


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/student/login", methods=["GET", "POST"])
def student_login():
    form = StudentLoginForm()
    if form.validate_on_submit():
        pin = form.pin.data
        # If district/school query params are provided, scope the search
        # Prefer form selections; fall back to query params
        district_id = form.district_id.data or request.args.get("district", type=int)
        school_id = form.school_id.data or request.args.get("school", type=int)

        query = Student.query
        if district_id:
            query = query.filter(
                Student.district_id == district_id
            )  # inherited from User
        if school_id:
            query = query.filter(Student.school_id == school_id)

        # Iterate candidates; at classroom scale this is small
        for s in query.all():
            if check_password_hash(s.pin_hash or s.password_hash, pin):
                session["student_id"] = s.id
                flash("Welcome, {}".format(s.character_name or s.username), "success")
                return redirect(url_for("main.index"))
        flash("Invalid student password.", "danger")
    # Filter schools dropdown when district is chosen
    if form.district_id.data and form.district_id.data != 0:
        schools = (
            School.query.filter_by(district_id=form.district_id.data)
            .order_by(School.name)
            .all()
        )
        form.school_id.choices = [(0, "Select School")] + [
            (s.id, s.name) for s in schools
        ]
    return render_template("student_login.html", form=form)


@bp.route("/student/logout")
def student_logout():
    if session.get("student_id"):
        session.pop("student_id")
        flash("Student logged out.", "info")
    return redirect(url_for("main.index"))


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

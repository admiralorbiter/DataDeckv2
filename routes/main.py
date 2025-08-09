from flask import redirect, render_template, session, url_for

from models import District, Observer, School, User, db

from .base import create_blueprint, observer_required, student_required

bp = create_blueprint("main")


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/observer/dashboard")
@observer_required
def observer_dashboard():
    observer_id = session.get("observer_id")
    observer = db.session.get(Observer, int(observer_id)) if observer_id else None
    if not observer:
        session.pop("observer_id", None)
        return redirect(url_for("observer_auth.observer_login"))

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
@observer_required
def observer_school(school_id: int):
    observer_id = session.get("observer_id")
    observer = db.session.get(Observer, int(observer_id)) if observer_id else None
    if not observer:
        session.pop("observer_id", None)
        return redirect(url_for("observer_auth.observer_login"))

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

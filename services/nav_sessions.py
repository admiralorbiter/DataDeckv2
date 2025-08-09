"""
Navigation session helpers for role-based session dropdowns.
This module provides functions to fetch appropriate sessions for each user role.
"""

from flask import session as flask_session
from flask_login import current_user

from models import School, Session, Student, User


def get_student_session():
    """
    Get the current session for a logged-in student.
    Returns the Session object if student is assigned to one, None otherwise.
    """
    student_id = flask_session.get("student_id")
    if not student_id:
        return None

    student = Student.query.get(student_id)
    if student and student.section_id:
        return student.section
    return None


def get_teacher_sessions(limit=10):
    """
    Get active sessions for the current teacher.
    Returns list of Session objects ordered by most recent.
    """
    if not current_user.is_authenticated or not current_user.is_teacher():
        return []

    return (
        Session.query.filter(
            Session.created_by_id == current_user.id,
            Session.is_archived == False,  # noqa: E712
        )
        .order_by(Session.created_at.desc())
        .limit(limit)
        .all()
    )


def get_observer_sessions(limit=20):
    """
    Get sessions visible to the current observer.
    Observers see sessions from their district/school scope.
    Returns list of Session objects grouped by school.
    """
    if not current_user.is_authenticated or not current_user.is_observer():
        return []

    # Observers see sessions from teachers in their school/district
    teacher_ids = (
        User.query.filter(
            User.role == User.Role.TEACHER,
            User.school_id == current_user.school_id,
            User.district_id == current_user.district_id,
        )
        .with_entities(User.id)
        .all()
    )

    teacher_ids = [t[0] for t in teacher_ids]

    if not teacher_ids:
        return []

    return (
        Session.query.filter(
            Session.created_by_id.in_(teacher_ids),
            Session.is_archived == False,  # noqa: E712
        )
        .order_by(Session.created_at.desc())
        .limit(limit)
        .all()
    )


def get_admin_sessions(limit=50):
    """
    Get sessions visible to admin/staff.
    Admins see all sessions, optionally grouped by district/school.
    Returns dict with structure: {district_name: {school_name: [sessions]}}
    """
    if not current_user.is_authenticated or not (
        current_user.is_admin() or current_user.is_staff()
    ):
        return {}

    # Get all active sessions with their creator's school/district info
    sessions = (
        Session.query.join(User, Session.created_by_id == User.id)
        .join(School, User.school_id == School.id)
        .filter(Session.is_archived == False)  # noqa: E712
        .order_by(Session.created_at.desc())
        .limit(limit)
        .all()
    )

    # Group by district -> school -> sessions
    grouped = {}
    for session in sessions:
        teacher = session.created_by
        if teacher.district and teacher.school:
            district_name = teacher.district.name
            school_name = teacher.school.name

            if district_name not in grouped:
                grouped[district_name] = {}
            if school_name not in grouped[district_name]:
                grouped[district_name][school_name] = []

            grouped[district_name][school_name].append(session)

    return grouped


def get_nav_sessions_for_current_user():
    """
    Get sessions appropriate for the current user's role.
    Returns dict with 'type' and 'data' keys for template consumption.
    """
    # Student session (PIN-based login)
    student_session = get_student_session()
    if student_session:
        return {"type": "student", "data": student_session}

    # Teacher sessions
    if current_user.is_authenticated and current_user.is_teacher():
        teacher_sessions = get_teacher_sessions()
        return {"type": "teacher", "data": teacher_sessions}

    # Observer sessions
    if current_user.is_authenticated and current_user.is_observer():
        observer_sessions = get_observer_sessions()
        return {"type": "observer", "data": observer_sessions}

    # Admin/staff sessions
    if current_user.is_authenticated and (
        current_user.is_admin() or current_user.is_staff()
    ):
        admin_sessions = get_admin_sessions()
        return {"type": "admin", "data": admin_sessions}

    return {"type": "none", "data": None}

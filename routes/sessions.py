from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from forms import StartSessionForm
from models import Module, Session, db
from services.session_service import SessionConflictError, SessionService

from .base import create_blueprint

bp = create_blueprint("sessions")


@bp.route("/sessions/start", methods=["GET", "POST"])
@login_required
def start_session():
    """Start a new session with conflict detection and resolution."""
    if not (
        current_user.is_teacher() or current_user.is_admin() or current_user.is_staff()
    ):
        flash("Only teachers can create sessions.", "danger")
        return redirect(url_for("main.index"))

    form = StartSessionForm()
    existing_session = None

    if form.validate_on_submit():
        try:
            # Check if user clicked "Archive and Create" button
            auto_archive = "archive_and_create" in request.form

            # Convert module string back to enum
            module_enum = Module(form.module.data)

            # Attempt to create session
            new_session, was_archived = SessionService.create_session(
                teacher=current_user,
                name=form.name.data,
                section=form.section.data,
                module=module_enum,
                character_set=form.character_set.data,
                auto_archive_existing=auto_archive,
            )

            # Generate students for the session
            students = SessionService.generate_students_for_session(
                new_session, count=20
            )

            # Commit everything
            db.session.commit()

            success_msg = (
                f"Session '{new_session.name}' created successfully "
                f"with {len(students)} students!"
            )
            if was_archived:
                success_msg += " Previous session was archived."
            flash(success_msg, "success")

            return redirect(
                url_for("sessions.session_detail", session_id=new_session.id)
            )

        except SessionConflictError as e:
            # Store the conflicting session to show options to user
            existing_session = e.existing_session
            flash(
                f"You already have an active session for Section {form.section.data}: "
                f"'{existing_session.name}'. Please choose an option below.",
                "warning",
            )

    return render_template(
        "sessions/start.html", form=form, existing_session=existing_session
    )


@bp.route("/sessions/<int:session_id>")
@login_required
def session_detail(session_id):
    """View session details with media and students."""
    session = Session.query.get_or_404(session_id)

    # Check ownership for teachers
    if current_user.is_teacher() and session.created_by_id != current_user.id:
        flash("You can only view your own sessions.", "danger")
        return redirect(url_for("sessions.list_sessions"))

    # Get students and media for this session
    students = session.students.all()
    media = session.media.limit(50).all()  # Latest 50 media items

    return render_template(
        "sessions/detail.html", session=session, students=students, media=media
    )


@bp.route("/sessions")
@login_required
def list_sessions():
    """List sessions for the current user."""
    if current_user.is_teacher():
        sessions = (
            Session.query.filter_by(created_by_id=current_user.id)
            .order_by(Session.created_at.desc())
            .all()
        )
    elif current_user.is_admin() or current_user.is_staff():
        sessions = Session.query.order_by(Session.created_at.desc()).all()
    else:
        flash("Access denied.", "danger")
        return redirect(url_for("main.index"))

    return render_template("sessions/list.html", sessions=sessions)


@bp.route("/sessions/<int:session_id>/archive", methods=["POST"])
@login_required
def archive_session(session_id):
    """Archive a session."""
    session = Session.query.get_or_404(session_id)

    # Check ownership for teachers
    if current_user.is_teacher() and session.created_by_id != current_user.id:
        flash("You can only archive your own sessions.", "danger")
        return redirect(url_for("sessions.list_sessions"))

    if session.is_archived:
        flash("Session is already archived.", "info")
    else:
        session.archive()
        db.session.commit()
        flash(f"Session '{session.name}' has been archived.", "success")

    return redirect(url_for("sessions.list_sessions"))


@bp.route("/sessions/<int:session_id>/unarchive", methods=["POST"])
@login_required
def unarchive_session(session_id):
    """Unarchive a session with conflict checking."""
    session = Session.query.get_or_404(session_id)

    # Check ownership for teachers
    if current_user.is_teacher() and session.created_by_id != current_user.id:
        flash("You can only unarchive your own sessions.", "danger")
        return redirect(url_for("sessions.list_sessions"))

    if not session.is_archived:
        flash("Session is not archived.", "info")
        return redirect(url_for("sessions.list_sessions"))

    # Check for conflicts before unarchiving
    existing_active = SessionService.validate_session_uniqueness(
        session.created_by_id, session.section, session.id
    )

    if existing_active:
        flash(
            f"Cannot unarchive: You already have an active session for "
            f"Section {session.section}: '{existing_active.name}'. Archive it first.",
            "danger",
        )
        return redirect(url_for("sessions.list_sessions"))

    # Safe to unarchive
    session.is_archived = False
    session.archived_at = None
    # Restore original name if it was saved
    if session.original_name:
        session.name = session.original_name
        session.original_name = None

    db.session.commit()
    flash(f"Session '{session.name}' has been unarchived.", "success")

    return redirect(url_for("sessions.list_sessions"))


@bp.route("/api/sessions/check-section", methods=["GET"])
@login_required
def check_section_availability():
    """API endpoint to check if a section has conflicts (for AJAX)."""
    section = request.args.get("section", type=int)
    if not section:
        return {"error": "Section parameter required"}, 400

    existing = SessionService.validate_session_uniqueness(current_user.id, section)

    if existing:
        return {
            "available": False,
            "conflict": {
                "id": existing.id,
                "name": existing.name,
                "module": existing.module.display_name,
                "created_at": existing.created_at.isoformat(),
            },
        }
    else:
        return {"available": True}

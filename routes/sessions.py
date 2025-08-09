from datetime import datetime

from flask import flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_

from forms import MediaFilterForm, SessionFilterForm, StartSessionForm
from models import Comment, Media, Session, Student, StudentMediaInteraction, db
from services.session_service import SessionConflictError, SessionService

from .base import create_blueprint, teacher_or_student_required

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

            # Get the selected module (form.module.data is now an integer ID)
            module_id = form.module.data

            # Attempt to create session
            new_session, was_archived = SessionService.create_session(
                teacher=current_user,
                name=form.name.data,
                section=form.section.data,
                module_id=module_id,
                character_set=form.character_set.data,
                auto_archive_existing=auto_archive,
            )

            # Generate students for the session
            students = SessionService.generate_students_for_session(
                new_session, count=form.student_count.data
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
@teacher_or_student_required
def session_detail(session_id):
    """View session details with media and students, including media filtering."""
    session_obj = Session.query.get_or_404(session_id)

    # Check access permissions
    if current_user.is_authenticated:
        # Teacher/admin access - check ownership
        if current_user.is_teacher() and session_obj.created_by_id != current_user.id:
            flash("You can only view your own sessions.", "danger")
            return redirect(url_for("sessions.list_sessions"))
    else:
        # Student access - check if they belong to this session
        student_id = session.get("student_id")
        if student_id:
            from models import Student

            student = Student.query.get(student_id)
            if not student or student.section_id != session_id:
                flash("You can only access your assigned session.", "warning")
                return redirect(url_for("main.index"))

    # Initialize media filter form
    media_filter_form = MediaFilterForm()
    media_filter_form.populate_tag_choices(session_id)

    # Get students for this session
    students = session_obj.students.all()

    # Build media query with filtering
    media_query = Media.query.filter(Media.session_id == session_id)

    # Apply filters from request args
    media_type_filter = request.args.get("media_type", "")
    graph_tag_filter = request.args.get("graph_tag", "")
    variable_tag_filter = request.args.get("variable_tag", "")
    is_graph_filter = request.args.get("is_graph", "")
    posted_by_filter = request.args.get("posted_by", "")

    # Set form data from query parameters for persistence
    if media_type_filter:
        media_filter_form.media_type.data = media_type_filter
    if graph_tag_filter:
        media_filter_form.graph_tag.data = graph_tag_filter
    if variable_tag_filter:
        media_filter_form.variable_tag.data = variable_tag_filter
    if is_graph_filter:
        media_filter_form.is_graph.data = is_graph_filter
    if posted_by_filter:
        media_filter_form.posted_by.data = posted_by_filter

    # Apply media type filter
    if media_type_filter:
        media_query = media_query.filter(Media.media_type == media_type_filter)

    # Apply graph tag filter
    if graph_tag_filter:
        media_query = media_query.filter(Media.graph_tag == graph_tag_filter)

    # Apply variable tag filter
    if variable_tag_filter:
        media_query = media_query.filter(Media.variable_tag == variable_tag_filter)

    # Apply is_graph filter
    if is_graph_filter == "true":
        media_query = media_query.filter(Media.is_graph.is_(True))
    elif is_graph_filter == "false":
        media_query = media_query.filter(Media.is_graph.is_(False))

    # Apply posted_by filter
    if posted_by_filter == "students":
        media_query = media_query.filter(Media.student_id.isnot(None))
    elif posted_by_filter == "teacher":
        media_query = media_query.filter(Media.posted_by_admin_id.isnot(None))

    # Pagination for media
    page = request.args.get("page", 1, type=int)
    per_page = 20  # Media items per page

    # Execute paginated query with ordering
    media_pagination = media_query.order_by(Media.uploaded_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    media = media_pagination.items
    media_total_count = media_pagination.total

    # Check if any filters are active
    has_media_filters = (
        media_type_filter
        or graph_tag_filter
        or variable_tag_filter
        or is_graph_filter
        or posted_by_filter
    )

    # Check if this is a student viewing
    viewing_student = None
    student_id = session.get("student_id")
    if student_id:
        viewing_student = Student.query.get(student_id)
        # Add student interaction data to each media item
        for item in media:
            interaction = StudentMediaInteraction.query.filter_by(
                student_id=student_id, media_id=item.id
            ).first()
            item.student_interactions = interaction

    # --- Session Analytics (teacher view primarily) ---
    # Aggregate reaction totals across all media in this session
    graph_total = (
        db.session.query(func.sum(Media.graph_likes))
        .filter(Media.session_id == session_id)
        .scalar()
        or 0
    )
    eye_total = (
        db.session.query(func.sum(Media.eye_likes))
        .filter(Media.session_id == session_id)
        .scalar()
        or 0
    )
    read_total = (
        db.session.query(func.sum(Media.read_likes))
        .filter(Media.session_id == session_id)
        .scalar()
        or 0
    )

    # Distinct students who reacted (any badge)
    reacted_students = (
        db.session.query(func.count(func.distinct(StudentMediaInteraction.student_id)))
        .join(Media, StudentMediaInteraction.media_id == Media.id)
        .filter(Media.session_id == session_id)
        .filter(
            or_(
                StudentMediaInteraction.liked_graph.is_(True),
                StudentMediaInteraction.liked_eye.is_(True),
                StudentMediaInteraction.liked_read.is_(True),
            )
        )
        .scalar()
        or 0
    )

    # Distinct students who commented; total comments
    student_commenters = (
        db.session.query(func.count(func.distinct(Comment.student_id)))
        .join(Media, Comment.media_id == Media.id)
        .filter(Media.session_id == session_id)
        .filter(Comment.is_admin.is_(False), Comment.student_id.isnot(None))
        .scalar()
        or 0
    )
    total_comments = (
        db.session.query(func.count(Comment.id))
        .join(Media, Comment.media_id == Media.id)
        .filter(Media.session_id == session_id)
        .scalar()
        or 0
    )

    # Top media by total reactions (top 3)
    score_expr = Media.graph_likes + Media.eye_likes + Media.read_likes
    top_media_q = (
        Media.query.filter(Media.session_id == session_id)
        .order_by(score_expr.desc(), Media.uploaded_at.desc())
        .limit(3)
        .all()
    )
    top_media = [
        {
            "id": m.id,
            "title": m.title,
            "score": (m.graph_likes + m.eye_likes + m.read_likes),
            "graph": m.graph_likes,
            "eye": m.eye_likes,
            "read": m.read_likes,
        }
        for m in top_media_q
    ]

    # Per-student participation table data
    student_participation = []
    for s in students:
        # Uploads by this student in this session
        uploads_count = (
            db.session.query(func.count(Media.id))
            .filter(Media.session_id == session_id, Media.student_id == s.id)
            .scalar()
            or 0
        )

        # Did the student react to any media in this session?
        reacted_any = (
            db.session.query(StudentMediaInteraction.id)
            .join(Media, StudentMediaInteraction.media_id == Media.id)
            .filter(
                Media.session_id == session_id,
                StudentMediaInteraction.student_id == s.id,
            )
            .filter(
                or_(
                    StudentMediaInteraction.liked_graph.is_(True),
                    StudentMediaInteraction.liked_eye.is_(True),
                    StudentMediaInteraction.liked_read.is_(True),
                )
            )
            .first()
            is not None
        )

        # Comment count by student in this session
        comments_count = (
            db.session.query(func.count(Comment.id))
            .join(Media, Comment.media_id == Media.id)
            .filter(
                Media.session_id == session_id,
                Comment.student_id == s.id,
                Comment.is_admin.is_(False),
            )
            .scalar()
            or 0
        )

        student_participation.append(
            {
                "id": s.id,
                "name": s.character_name,
                "uploads": uploads_count,
                "reacted": reacted_any,
                "comments": comments_count,
            }
        )

    analytics = {
        "reaction_totals": {
            "graph": graph_total,
            "eye": eye_total,
            "read": read_total,
            "total": graph_total + eye_total + read_total,
        },
        "participation": {
            "students_total": len(students),
            "students_reacted": reacted_students,
            "students_commented": student_commenters,
            "comments_total": total_comments,
        },
        "top_media": top_media,
        "students": student_participation,
    }

    return render_template(
        "sessions/detail.html",
        session_data=session_obj,
        students=students,
        media=media,
        media_filter_form=media_filter_form,
        media_pagination=media_pagination,
        media_total_count=media_total_count,
        has_media_filters=has_media_filters,
        viewing_student=viewing_student,
        analytics=analytics,
    )


@bp.route("/sessions/<int:session_id>/reactions/reset", methods=["POST"])
@login_required
def reset_session_reactions(session_id: int):
    """Bulk reset all reactions for every media item
    in a session (teacher/admin/staff)."""
    session_obj = Session.query.get_or_404(session_id)

    # Permission: teacher who owns the session, or admin/staff
    if current_user.is_teacher():
        if session_obj.created_by_id != current_user.id:
            flash("You can only manage reactions for your own sessions.", "danger")
            return redirect(url_for("sessions.session_detail", session_id=session_id))
    elif not (
        getattr(current_user, "is_admin", lambda: False)()
        or getattr(current_user, "is_staff", lambda: False)()
    ):
        flash("Access denied.", "danger")
        return redirect(url_for("sessions.session_detail", session_id=session_id))

    try:
        # Reset all interactions for media in this session
        media_ids = [m.id for m in session_obj.media.all()]
        if media_ids:
            StudentMediaInteraction.query.filter(
                StudentMediaInteraction.media_id.in_(media_ids)
            ).update(
                {
                    StudentMediaInteraction.liked_graph: False,
                    StudentMediaInteraction.liked_eye: False,
                    StudentMediaInteraction.liked_read: False,
                },
                synchronize_session=False,
            )

            # Reset denormalized counts on each media
            Media.query.filter(Media.id.in_(media_ids)).update(
                {
                    Media.graph_likes: 0,
                    Media.eye_likes: 0,
                    Media.read_likes: 0,
                },
                synchronize_session=False,
            )
        db.session.commit()
        flash("All reactions cleared for this session.", "success")
    except Exception:
        db.session.rollback()
        flash("Failed to clear reactions for this session.", "danger")
    return redirect(url_for("sessions.session_detail", session_id=session_id))


@bp.route(
    "/sessions/<int:session_id>/students/<int:student_id>/reactions/reset",
    methods=["POST"],
)
@login_required
def reset_student_reactions(session_id: int, student_id: int):
    """Inline control: reset a single student's reactions within the session."""
    session_obj = Session.query.get_or_404(session_id)
    student = Student.query.get_or_404(student_id)

    # Permission: teacher who owns the session, or admin/staff
    if current_user.is_teacher():
        if session_obj.created_by_id != current_user.id:
            flash("You can only manage your own sessions.", "danger")
            return redirect(url_for("sessions.session_detail", session_id=session_id))
    elif not (
        getattr(current_user, "is_admin", lambda: False)()
        or getattr(current_user, "is_staff", lambda: False)()
    ):
        flash("Access denied.", "danger")
        return redirect(url_for("sessions.session_detail", session_id=session_id))

    # Ensure student belongs to session
    if student.section_id != session_id:
        flash("Student does not belong to this session.", "warning")
        return redirect(url_for("sessions.session_detail", session_id=session_id))

    try:
        # Find all interactions for this student's media within this session
        media_ids = [m.id for m in session_obj.media.all()]
        if media_ids:
            StudentMediaInteraction.query.filter(
                StudentMediaInteraction.student_id == student_id,
                StudentMediaInteraction.media_id.in_(media_ids),
            ).update(
                {
                    StudentMediaInteraction.liked_graph: False,
                    StudentMediaInteraction.liked_eye: False,
                    StudentMediaInteraction.liked_read: False,
                },
                synchronize_session=False,
            )

            # Recompute media denormalized counts efficiently
            for m in session_obj.media.all():
                m.graph_likes = StudentMediaInteraction.query.filter_by(
                    media_id=m.id, liked_graph=True
                ).count()
                m.eye_likes = StudentMediaInteraction.query.filter_by(
                    media_id=m.id, liked_eye=True
                ).count()
                m.read_likes = StudentMediaInteraction.query.filter_by(
                    media_id=m.id, liked_read=True
                ).count()

        db.session.commit()
        flash(f"Cleared reactions for {student.character_name}.", "success")
    except Exception:
        db.session.rollback()
        flash("Failed to clear reactions for this student.", "danger")

    return redirect(url_for("sessions.session_detail", session_id=session_id))


@bp.route("/sessions")
@login_required
def list_sessions():
    """List sessions for the current user with optional filtering."""
    # Initialize filter form
    filter_form = SessionFilterForm()
    filter_form.populate_module_choices()

    # Build base query based on user role
    if current_user.is_teacher():
        query = Session.query.filter_by(created_by_id=current_user.id)
    elif current_user.is_admin() or current_user.is_staff():
        query = Session.query
    else:
        flash("Access denied.", "danger")
        return redirect(url_for("main.index"))

    # Apply filters from query parameters
    status_filter = request.args.get("status", "")
    module_filter = request.args.get("module", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    # Set form data from query parameters
    if status_filter:
        filter_form.status.data = status_filter
    if module_filter:
        filter_form.module.data = int(module_filter) if module_filter else None
    if date_from:
        try:
            filter_form.date_from.data = datetime.strptime(date_from, "%Y-%m-%d").date()
        except ValueError:
            pass
    if date_to:
        try:
            filter_form.date_to.data = datetime.strptime(date_to, "%Y-%m-%d").date()
        except ValueError:
            pass

    # Apply status filter
    if status_filter == "active":
        query = query.filter(
            Session.is_archived.is_(False), Session.is_paused.is_(False)
        )
    elif status_filter == "archived":
        query = query.filter(Session.is_archived.is_(True))
    elif status_filter == "paused":
        query = query.filter(Session.is_paused.is_(True))

    # Apply module filter
    if module_filter:
        query = query.filter(Session.module_id == int(module_filter))

    # Apply date filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(Session.created_at >= from_date)
        except ValueError:
            flash("Invalid 'from' date format.", "warning")

    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d")
            # Add one day to include the entire end date
            to_date = to_date.replace(hour=23, minute=59, second=59)
            query = query.filter(Session.created_at <= to_date)
        except ValueError:
            flash("Invalid 'to' date format.", "warning")

    # Pagination parameters
    page = request.args.get("page", 1, type=int)
    per_page = 12  # Number of sessions per page (3 rows × 4 columns)

    # Execute paginated query with ordering
    pagination = query.order_by(Session.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    sessions = pagination.items
    total_count = pagination.total

    return render_template(
        "sessions/list.html",
        sessions=sessions,
        filter_form=filter_form,
        pagination=pagination,
        total_count=total_count,
        has_filters=(status_filter or module_filter or date_from or date_to),
    )


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


@bp.route("/sessions/<int:session_id>/delete", methods=["POST"])
@login_required
def delete_session(session_id):
    """Permanently delete a session with all its data."""
    session = Session.query.get_or_404(session_id)

    # Check ownership for teachers
    if current_user.is_teacher() and session.created_by_id != current_user.id:
        flash("You can only delete your own sessions.", "danger")
        return redirect(url_for("sessions.list_sessions"))

    # Only allow deletion of archived sessions to prevent accidental data loss
    if not session.is_archived:
        flash(
            "Sessions must be archived before they can be deleted.",
            "Archive this session first. warning",
        )
        return redirect(url_for("sessions.list_sessions"))

    try:
        session_name = session.name

        # Delete related data first (cascade should handle this, but being explicit)
        # Students and media will be cascade deleted by the database relationships

        # Delete the session
        db.session.delete(session)
        db.session.commit()

        flash(f"Session '{session_name}' has been permanently deleted.", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting session: {str(e)}", "danger")

    return redirect(url_for("sessions.list_sessions"))


@bp.route("/sessions/<int:session_id>/pause", methods=["POST"])
@login_required
def pause_session(session_id):
    """Pause a session to temporarily prevent student access."""
    session = Session.query.get_or_404(session_id)

    # Check ownership for teachers
    if current_user.is_teacher() and session.created_by_id != current_user.id:
        flash("You can only pause your own sessions.", "danger")
        return redirect(url_for("sessions.list_sessions"))

    # Can't pause archived sessions
    if session.is_archived:
        flash("Cannot pause archived sessions.", "warning")
        return redirect(url_for("sessions.list_sessions"))

    # Check if already paused
    if session.is_paused:
        flash("Session is already paused.", "info")
        return redirect(url_for("sessions.list_sessions"))

    try:
        session.is_paused = True
        db.session.commit()
        flash(
            f"Session '{session.name}' has been paused. Students cannot access it.",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error pausing session: {str(e)}", "danger")

    return redirect(url_for("sessions.list_sessions"))


@bp.route("/sessions/<int:session_id>/unpause", methods=["POST"])
@login_required
def unpause_session(session_id):
    """Resume/unpause a session to allow student access."""
    session = Session.query.get_or_404(session_id)

    # Check ownership for teachers
    if current_user.is_teacher() and session.created_by_id != current_user.id:
        flash("You can only resume your own sessions.", "danger")
        return redirect(url_for("sessions.list_sessions"))

    # Can't unpause archived sessions
    if session.is_archived:
        flash("Cannot resume archived sessions. Unarchive first.", "warning")
        return redirect(url_for("sessions.list_sessions"))

    # Check if already active
    if not session.is_paused:
        flash("Session is already active.", "info")
        return redirect(url_for("sessions.list_sessions"))

    try:
        session.is_paused = False
        db.session.commit()
        flash(
            f"Session '{session.name}' has been resumed. Students can now access it.",
            "success",
        )
    except Exception as e:
        db.session.rollback()
        flash(f"Error resuming session: {str(e)}", "danger")

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
                "module": existing.module.name,
                "created_at": existing.created_at.isoformat(),
            },
        }
    else:
        return {"available": True}

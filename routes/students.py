"""Student management routes for M4 implementation."""

from datetime import datetime

from flask import (
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from models import db
from models.media import Media
from services.pin_cards_service import PinCardsService
from services.student_service import StudentService

from .base import create_blueprint

bp = create_blueprint("students")


@bp.route("/students")
@login_required
def student_list():
    """Display list of students for the current teacher.

    Shows all students across all sessions for the logged-in teacher.
    Supports filtering by session if session_id is provided as query parameter.
    """
    if not current_user.is_teacher():
        flash("Access denied. Teacher account required.", "danger")
        return redirect(url_for("main.index"))

    session_id = request.args.get("session_id", type=int)
    students = StudentService.get_students_for_teacher(
        teacher_id=current_user.id, session_id=session_id
    )

    # Get session info if filtering by session
    session = None
    if session_id:
        from models.session import Session

        session = Session.query.filter(
            Session.id == session_id, Session.created_by_id == current_user.id
        ).first()

        if not session:
            flash("Session not found or access denied.", "danger")
            return redirect(url_for("students.student_list"))

    return render_template(
        "students/list.html",
        students=students,
        session=session,
        total_count=len(students),
    )


@bp.route("/students/<int:student_id>")
@login_required
def student_detail(student_id):
    """View individual student details and portfolio."""
    if not current_user.is_teacher():
        flash("Access denied. Teacher account required.", "danger")
        return redirect(url_for("main.index"))

    student = StudentService.get_student_with_ownership_check(
        student_id, current_user.id
    )

    if not student:
        flash("Student not found or access denied.", "danger")
        return redirect(url_for("students.student_list"))

    # Get student portfolio data
    portfolio = StudentService.get_student_portfolio(student_id, current_user.id)

    if not portfolio:
        flash("Unable to load student portfolio.", "warning")
        portfolio = {
            "student": student,
            "uploaded_media": [],
            "interactions": [],
            "comments": [],
            "stats": {
                "total_uploads": 0,
                "total_reactions_given": 0,
                "total_reactions_received": 0,
                "total_comments": 0,
                "recent_activity_count": 0,
            },
        }

    return render_template("students/detail.html", **portfolio)


@bp.route("/students/<int:student_id>/delete", methods=["DELETE", "POST"])
@login_required
def delete_student(student_id):
    """Delete a student with ownership verification."""
    if not current_user.is_teacher():
        return jsonify({"success": False, "message": "Access denied"}), 403

    success = StudentService.delete_student_with_ownership_check(
        student_id, current_user.id
    )

    if success:
        db.session.commit()
        message = "Student deleted successfully"

        if request.method == "POST":  # Form submission
            flash(message, "success")
            return redirect(request.referrer or url_for("students.student_list"))
        else:  # AJAX request
            return jsonify({"success": True, "message": message})
    else:
        message = "Student not found or access denied"

        if request.method == "POST":
            flash(message, "danger")
            return redirect(request.referrer or url_for("students.student_list"))
        else:
            return jsonify({"success": False, "message": message}), 404


@bp.route("/students/<int:student_id>/reset-pin", methods=["POST"])
@login_required
def reset_student_pin(student_id):
    """Reset a student's PIN and return the new PIN."""
    if not current_user.is_teacher():
        return jsonify({"success": False, "message": "Access denied"}), 403

    new_pin = StudentService.reset_student_pin(student_id, current_user.id)

    if new_pin:
        db.session.commit()
        return jsonify(
            {"success": True, "message": "PIN reset successfully", "new_pin": new_pin}
        )
    else:
        return (
            jsonify(
                {"success": False, "message": "Student not found or access denied"}
            ),
            404,
        )


@bp.route("/students/delete-multiple", methods=["POST"])
@login_required
def delete_multiple_students():
    """Delete multiple students in bulk."""
    if not current_user.is_teacher():
        return jsonify({"success": False, "message": "Access denied"}), 403

    data = request.get_json()
    student_ids = data.get("student_ids", [])

    if not student_ids:
        return jsonify({"success": False, "message": "No students selected"}), 400

    deleted_count = 0
    for student_id in student_ids:
        if StudentService.delete_student_with_ownership_check(
            student_id, current_user.id
        ):
            deleted_count += 1

    if deleted_count > 0:
        db.session.commit()

    return jsonify(
        {
            "success": deleted_count > 0,
            "message": (
                f"{deleted_count} students deleted successfully"
                if deleted_count > 0
                else "No students were deleted"
            ),
            "deleted_count": deleted_count,
        }
    )


@bp.route("/students/session/<int:session_id>/summary")
@login_required
def session_student_summary(session_id):
    """Get student summary for a specific session (AJAX endpoint)."""
    if not current_user.is_teacher():
        return jsonify({"error": "Access denied"}), 403

    summary = StudentService.get_session_student_summary(session_id, current_user.id)

    if summary is None:
        return jsonify({"error": "Session not found or access denied"}), 404

    return jsonify(summary)


@bp.route("/students/pin-cards/<int:session_id>")
@login_required
def generate_pin_cards(session_id):
    """Generate printable PIN cards for a session."""
    if not current_user.is_teacher():
        flash("Access denied. Teacher account required.", "danger")
        return redirect(url_for("main.index"))

    result = PinCardsService.generate_pin_cards_pdf(session_id, current_user.id)

    if result is None:
        flash("Session not found or access denied.", "danger")
        return redirect(url_for("students.student_list"))

    pdf_bytes, filename = result

    # Commit the PIN changes to database
    db.session.commit()

    # Return PDF as download
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


@bp.route("/students/pin-cards/<int:session_id>/preview")
@login_required
def preview_pin_cards(session_id):
    """Preview PIN cards information before generating PDF."""
    if not current_user.is_teacher():
        flash("Access denied. Teacher account required.", "danger")
        return redirect(url_for("main.index"))

    summary = PinCardsService.get_session_pin_summary(session_id, current_user.id)

    if summary is None:
        flash("Session not found or access denied.", "danger")
        return redirect(url_for("students.student_list"))

    return render_template(
        "students/pin_cards_preview.html",
        session=summary["session"],
        students=summary["students"],
        total_students=summary["total_students"],
    )


@bp.route("/students/analytics")
@login_required
def student_analytics():
    """Get analytics data for teacher's students."""
    if not current_user.is_teacher():
        return jsonify({"success": False, "message": "Access denied"}), 403

    try:
        # Get all students for this teacher
        students = StudentService.get_students_for_teacher(current_user.id)

        if not students:
            return jsonify(
                {
                    "success": True,
                    "analytics": {
                        "active_students": 0,
                        "total_uploads": 0,
                        "engagement_rate": 0,
                    },
                }
            )

        # Get students in active sessions
        active_students = 0
        for student in students:
            if student.section and not student.section.is_archived:
                active_students += 1

        # Get total uploads by teacher's students
        student_ids = [s.id for s in students]
        total_uploads = Media.query.filter(Media.student_id.in_(student_ids)).count()

        # Calculate engagement rate (students with uploads / total students)
        students_with_uploads = (
            Media.query.filter(Media.student_id.in_(student_ids))
            .distinct(Media.student_id)
            .count()
        )

        engagement_rate = round(
            (students_with_uploads / len(students) * 100) if students else 0, 1
        )

        return jsonify(
            {
                "success": True,
                "analytics": {
                    "active_students": active_students,
                    "total_uploads": total_uploads,
                    "engagement_rate": engagement_rate,
                },
            }
        )

    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": f"Error calculating analytics: {str(e)}"}
            ),
            500,
        )


@bp.route("/students/analytics/dashboard")
@login_required
def analytics_dashboard():
    """Display the analytics dashboard page."""
    if not current_user.is_teacher():
        flash("Access denied. Teacher account required.", "danger")
        return redirect(url_for("main.index"))

    return render_template("students/analytics.html")


@bp.route("/students/analytics/detailed")
@login_required
def detailed_analytics():
    """Get detailed analytics data for teacher's students."""
    if not current_user.is_teacher():
        return jsonify({"success": False, "message": "Access denied"}), 403

    try:

        from models.media import Media
        from models.session import Session

        # Get all students for this teacher
        students = StudentService.get_students_for_teacher(current_user.id)
        student_ids = [s.id for s in students]

        # Get session performance data
        sessions = (
            Session.query.filter(Session.created_by_id == current_user.id)
            .order_by(Session.created_at.desc())
            .limit(10)
            .all()
        )

        session_data = []
        for session in sessions:
            session_data.append(
                {
                    "name": session.name,
                    "section": session.section,
                    "student_count": session.students.count(),
                    "is_archived": session.is_archived,
                    "is_paused": session.is_paused,
                }
            )

        # Get character theme distribution
        theme_distribution = {}
        for student in students:
            theme = PinCardsService._get_character_theme(student.character_name)
            theme_distribution[theme] = theme_distribution.get(theme, 0) + 1

        # Get top performing students
        top_students = []
        for student in students:
            uploads = Media.query.filter(Media.student_id == student.id).count()

            # Get reactions given by this student
            from models.student_media_interaction import StudentMediaInteraction

            interactions = StudentMediaInteraction.query.filter(
                StudentMediaInteraction.student_id == student.id
            ).all()

            reactions = sum(
                [
                    (1 if interaction.liked_graph else 0)
                    + (1 if interaction.liked_eye else 0)
                    + (1 if interaction.liked_read else 0)
                    for interaction in interactions
                ]
            )

            total_activity = uploads + reactions

            if total_activity > 0:
                top_students.append(
                    {
                        "character_name": student.character_name,
                        "uploads": uploads,
                        "reactions": reactions,
                        "total_activity": total_activity,
                    }
                )

        # Sort by total activity and take top 10
        top_students.sort(key=lambda x: x["total_activity"], reverse=True)
        top_students = top_students[:10]

        # Get recent activity (last 10 uploads/comments)
        recent_media = (
            Media.query.filter(Media.student_id.in_(student_ids))
            .order_by(Media.uploaded_at.desc())
            .limit(5)
            .all()
        )

        recent_activity = []
        for media in recent_media:
            student = next((s for s in students if s.id == media.student_id), None)
            if student:
                time_ago = get_time_ago(media.uploaded_at)
                recent_activity.append(
                    {
                        "type": "upload",
                        "student_name": student.character_name,
                        "action": f'uploaded "{media.title}"',
                        "time_ago": time_ago,
                    }
                )

        return jsonify(
            {
                "success": True,
                "analytics": {
                    "total_students": len(students),
                    "sessions": session_data,
                    "themes": theme_distribution,
                    "top_students": top_students,
                    "recent_activity": recent_activity,
                },
            }
        )

    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Error calculating detailed analytics: {str(e)}",
                }
            ),
            500,
        )


def get_time_ago(timestamp):
    """Convert timestamp to human-readable time ago format."""
    now = datetime.now()
    if timestamp.tzinfo is None:
        # If timestamp is naive, assume it's in the same timezone as now
        timestamp = timestamp.replace(tzinfo=now.tzinfo) if now.tzinfo else timestamp

    diff = now - timestamp

    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"

#!/usr/bin/env python3
"""
Media routes - Handle media upload, viewing, editing, and deletion.
Supports both individual uploads and project galleries (Data Decks).
"""

from flask import (
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user

from forms import MediaEditForm, ProjectGalleryUploadForm, SingleMediaUploadForm
from models import Media, Student, db
from services.media_service import MediaService

from .base import create_blueprint, student_required, teacher_or_student_required

bp = create_blueprint("media")


@bp.route("/media/upload/single", methods=["GET", "POST"])
@student_required
def upload_single():
    """Upload a single media item (student only)."""
    form = SingleMediaUploadForm()

    # Get current student
    student_id = session.get("student_id")
    student = Student.query.get_or_404(student_id)
    session_obj = student.section

    if not session_obj:
        flash("You are not assigned to an active session.", "warning")
        return redirect(url_for("main.index"))

    if form.validate_on_submit():
        try:
            # Prepare tags dictionary
            tags = {
                "is_graph": form.is_graph.data,
                "graph_tag": form.graph_tag.data if form.graph_tag.data else None,
                "variable_tag": (
                    form.variable_tag.data if form.variable_tag.data else None
                ),
            }

            # Create media item
            media = MediaService.create_single_media(
                session_id=session_obj.id,
                student_id=student_id,
                file=form.file.data,
                title=form.title.data,
                description=form.description.data,
                tags=tags,
            )

            # Save to database
            db.session.commit()

            flash(f"Successfully uploaded '{media.title}'!", "success")
            return redirect(
                url_for("sessions.session_detail", session_id=session_obj.id)
            )

        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while uploading. Please try again.", "danger")
            current_app.logger.error(f"Media upload error: {e}")

    return render_template(
        "media/upload_single.html", form=form, student=student, session_data=session_obj
    )


@bp.route("/media/upload/project", methods=["GET", "POST"])
@student_required
def upload_project():
    """Upload a project gallery/Data Deck (student only)."""
    form = ProjectGalleryUploadForm()

    # Get current student
    student_id = session.get("student_id")
    student = Student.query.get_or_404(student_id)
    session_obj = student.section

    if not session_obj:
        flash("You are not assigned to an active session.", "warning")
        return redirect(url_for("main.index"))

    if form.validate_on_submit():
        try:
            # Validate file count (1-10 images)
            files = form.files.data
            if len(files) < 1:
                flash("Please select at least 1 image.", "danger")
                return render_template(
                    "media/upload_project.html",
                    form=form,
                    student=student,
                    session_data=session_obj,
                )

            if len(files) > 10:
                flash("You can upload a maximum of 10 images per Data Deck.", "danger")
                return render_template(
                    "media/upload_project.html",
                    form=form,
                    student=student,
                    session_data=session_obj,
                )

            # Prepare tags dictionary
            tags = {
                "is_graph": form.is_graph.data,
                "graph_tag": form.graph_tag.data if form.graph_tag.data else None,
                "variable_tag": (
                    form.variable_tag.data if form.variable_tag.data else None
                ),
            }

            # Create project gallery
            media_items = MediaService.create_project_gallery(
                session_id=session_obj.id,
                student_id=student_id,
                files=files,
                title=form.title.data,
                description=form.description.data,
                tags=tags,
            )

            # Save to database
            db.session.commit()

            flash(
                f"Successfully created Data Deck '{form.title.data}' "
                f"with {len(media_items)} images!",
                "success",
            )
            return redirect(
                url_for("sessions.session_detail", session_id=session_obj.id)
            )

        except ValueError as e:
            flash(str(e), "danger")
        except Exception as e:
            db.session.rollback()
            flash(
                "An error occurred while creating your Data Deck. Please try again.",
                "danger",
            )
            current_app.logger.error(f"Project upload error: {e}")

    return render_template(
        "media/upload_project.html",
        form=form,
        student=student,
        session_data=session_obj,
    )


@bp.route("/media/<int:media_id>")
@teacher_or_student_required
def media_detail(media_id):
    """View individual media item details."""
    media = Media.query.get_or_404(media_id)

    # Check access permissions
    if current_user.is_authenticated:
        # Teacher/admin access - check session ownership
        if current_user.is_teacher() and media.session.created_by_id != current_user.id:
            flash("You can only view media from your own sessions.", "danger")
            return redirect(url_for("main.index"))
    else:
        # Student access - check if they belong to this session
        student_id = session.get("student_id")
        if student_id:
            student = Student.query.get(student_id)
            if not student or student.section_id != media.session_id:
                flash("You can only view media from your session.", "warning")
                return redirect(url_for("main.index"))

    # If this is part of a project, get all project images
    project_images = []
    if media.is_project and media.project_group:
        project_images = MediaService.get_project_gallery(media.project_group)

    return render_template(
        "media/detail.html",
        media=media,
        project_images=project_images,
        is_student_view=not current_user.is_authenticated,
    )


@bp.route("/media/<int:media_id>/edit", methods=["GET", "POST"])
@teacher_or_student_required
def edit_media(media_id):
    """Edit media metadata and tags."""
    media = Media.query.get_or_404(media_id)
    form = MediaEditForm(obj=media)

    # Check permissions
    can_edit = False
    is_teacher = False

    if current_user.is_authenticated:
        # Teacher/admin can edit media in their sessions
        if current_user.is_teacher() and media.session.created_by_id == current_user.id:
            can_edit = True
            is_teacher = True
    else:
        # Students can edit their own media
        student_id = session.get("student_id")
        if student_id and media.student_id == student_id:
            can_edit = True

    if not can_edit:
        flash("You don't have permission to edit this media.", "danger")
        return redirect(url_for("media.media_detail", media_id=media_id))

    # Pre-populate form with current values
    form.is_graph.data = media.is_graph
    form.graph_tag.data = media.graph_tag
    form.variable_tag.data = media.variable_tag

    if form.validate_on_submit():
        try:
            # Prepare tags dictionary
            tags = {
                "is_graph": form.is_graph.data,
                "graph_tag": form.graph_tag.data if form.graph_tag.data else None,
                "variable_tag": (
                    form.variable_tag.data if form.variable_tag.data else None
                ),
            }

            # Update media
            requester_id = (
                current_user.id
                if current_user.is_authenticated
                else session.get("student_id")
            )
            success = MediaService.update_media_tags(
                media_id=media_id,
                tags=tags,
                requester_id=requester_id,
                is_teacher=is_teacher,
            )

            if success:
                # Also update title and description directly
                media.title = form.title.data
                media.description = form.description.data
                db.session.commit()

                flash("Media updated successfully!", "success")
                return redirect(url_for("media.media_detail", media_id=media_id))
            else:
                flash("Failed to update media.", "danger")

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating media.", "danger")
            current_app.logger.error(f"Media edit error: {e}")

    return render_template(
        "media/edit.html",
        form=form,
        media=media,
        is_student_view=not current_user.is_authenticated,
    )


@bp.route("/media/<int:media_id>/delete", methods=["POST", "DELETE"])
@teacher_or_student_required
def delete_media(media_id):
    """Delete a media item."""
    media = Media.query.get_or_404(media_id)

    # Determine requester info
    is_teacher = current_user.is_authenticated and current_user.is_teacher()
    requester_id = (
        current_user.id if current_user.is_authenticated else session.get("student_id")
    )

    if not requester_id:
        return jsonify({"success": False, "message": "Authentication required"}), 401

    try:
        success = MediaService.delete_media(
            media_id=media_id, requester_id=requester_id, is_teacher=is_teacher
        )

        if success:
            db.session.commit()

            if request.is_json:
                return jsonify(
                    {
                        "success": True,
                        "message": (
                            f"{'Project' if media.is_project else 'Media'} "
                            "deleted successfully"
                        ),
                    }
                )
            else:
                flash(
                    f"{'Data Deck' if media.is_project else 'Image'} "
                    "deleted successfully!",
                    "success",
                )
                return redirect(
                    url_for("sessions.session_detail", session_id=media.session_id)
                )
        else:
            if request.is_json:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Permission denied or media not found",
                        }
                    ),
                    403,
                )
            else:
                flash("You don't have permission to delete this media.", "danger")
                return redirect(url_for("media.media_detail", media_id=media_id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Media deletion error: {e}")

        if request.is_json:
            return jsonify({"success": False, "message": "An error occurred"}), 500
        else:
            flash("An error occurred while deleting media.", "danger")
            return redirect(url_for("media.media_detail", media_id=media_id))


@bp.route("/media/my-uploads")
@student_required
def my_uploads():
    """View all uploads by the current student."""
    student_id = session.get("student_id")
    student = Student.query.get_or_404(student_id)

    # Get all media by this student
    media_items = MediaService.get_student_media(student_id)

    # Get upload statistics
    stats = MediaService.get_upload_stats(student_id)

    return render_template(
        "media/my_uploads.html", student=student, media_items=media_items, stats=stats
    )


@bp.route("/media/project/<string:project_group>")
@teacher_or_student_required
def project_gallery(project_group):
    """View a complete project gallery."""
    project_images = MediaService.get_project_gallery(project_group)

    if not project_images:
        flash("Project not found.", "danger")
        return redirect(url_for("main.index"))

    # Check access permissions using the first image
    first_media = project_images[0]

    if current_user.is_authenticated:
        # Teacher/admin access
        if (
            current_user.is_teacher()
            and first_media.session.created_by_id != current_user.id
        ):
            flash("You can only view projects from your own sessions.", "danger")
            return redirect(url_for("main.index"))
    else:
        # Student access
        student_id = session.get("student_id")
        if student_id:
            student = Student.query.get(student_id)
            if not student or student.section_id != first_media.session_id:
                flash("You can only view projects from your session.", "warning")
                return redirect(url_for("main.index"))

    return render_template(
        "media/project_gallery.html",
        project_images=project_images,
        project_title=first_media.title,
        is_student_view=not current_user.is_authenticated,
    )

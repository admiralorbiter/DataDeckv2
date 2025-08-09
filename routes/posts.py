#!/usr/bin/env python3
"""
Posts routes - Handle post details and comment functionality.
Posts are essentially media items with comment threads.
"""

from flask import current_app, flash, redirect, render_template, session, url_for
from flask_login import current_user

from forms import CommentForm
from models import Comment, Media, Student, StudentMediaInteraction, User, db

from .base import create_blueprint, teacher_or_student_required

bp = create_blueprint("posts")


@bp.route("/post/<int:media_id>")
@teacher_or_student_required
def post_detail(media_id):
    """View post detail with media, poster info, and comment thread."""
    media = Media.query.get_or_404(media_id)

    # Check access permissions
    if current_user.is_authenticated:
        # Teacher/admin access - check session ownership
        if current_user.is_teacher() and media.session.created_by_id != current_user.id:
            flash("You can only view posts from your own sessions.", "danger")
            return redirect(url_for("main.index"))
    else:
        # Student access - check if they belong to this session
        student_id = session.get("student_id")
        if student_id:
            student = Student.query.get(student_id)
            if not student or student.section_id != media.session_id:
                flash("You can only view posts from your session.", "warning")
                return redirect(url_for("main.index"))

    # Get all comments for this media, ordered by creation time
    # We'll handle nesting in the template
    comments = (
        Comment.query.filter_by(media_id=media_id)
        .order_by(Comment.created_at.asc())
        .all()
    )

    # Build nested comment structure
    comment_tree = _build_comment_tree(comments)

    # Get poster information
    poster_info = _get_poster_info(media)

    # Get reaction counts and current user's interactions
    interaction_info = _get_interaction_info(media)

    # Create comment form
    comment_form = CommentForm()

    return render_template(
        "posts/detail.html",
        media=media,
        poster_info=poster_info,
        comments=comment_tree,
        interaction_info=interaction_info,
        comment_form=comment_form,
        is_student_view=not current_user.is_authenticated,
    )


@bp.route("/post/<int:media_id>/comment", methods=["POST"])
@teacher_or_student_required
def add_comment(media_id):
    """Add a comment to a post."""
    media = Media.query.get_or_404(media_id)
    form = CommentForm()

    # Check access permissions (same as post_detail)
    if current_user.is_authenticated:
        if current_user.is_teacher() and media.session.created_by_id != current_user.id:
            flash("You can only comment on posts from your own sessions.", "danger")
            return redirect(url_for("main.index"))
    else:
        student_id = session.get("student_id")
        if student_id:
            student = Student.query.get(student_id)
            if not student or student.section_id != media.session_id:
                flash("You can only comment on posts from your session.", "warning")
                return redirect(url_for("main.index"))

    if form.validate_on_submit():
        try:
            # Determine commenter info
            if current_user.is_authenticated:
                # Teacher/Admin comment
                comment = Comment(
                    media_id=media_id,
                    parent_id=form.parent_id.data if form.parent_id.data else None,
                    text=form.text.data,
                    name=f"{current_user.first_name} {current_user.last_name}",
                    is_admin=True,
                    admin_avatar=getattr(current_user, "profile_picture", None),
                )
            else:
                # Student comment
                student_id = session.get("student_id")
                student = Student.query.get(student_id)

                comment = Comment(
                    media_id=media_id,
                    parent_id=form.parent_id.data if form.parent_id.data else None,
                    text=form.text.data,
                    name=student.name,
                    device_id=session.get("device_id"),  # Optional tracking
                    is_admin=False,
                    student_id=student_id,
                )

                # Increment comment count in StudentMediaInteraction
                _increment_comment_count(student_id, media_id)

            db.session.add(comment)
            db.session.commit()

            flash("Comment added successfully!", "success")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Comment creation error: {e}")
            flash("An error occurred while adding your comment.", "danger")

    # Redirect back to post detail
    return redirect(url_for("posts.post_detail", media_id=media_id))


def _build_comment_tree(comments):
    """Build a nested structure for comments and replies."""
    comment_dict = {comment.id: comment for comment in comments}
    tree = []

    for comment in comments:
        # Add a replies list to each comment
        comment.replies = []

        if comment.parent_id is None:
            # Top-level comment
            tree.append(comment)
        else:
            # Reply - add to parent's replies
            if comment.parent_id in comment_dict:
                comment_dict[comment.parent_id].replies.append(comment)

    return tree


def _get_poster_info(media):
    """Get information about who posted the media."""
    if media.student_id:
        student = Student.query.get(media.student_id)
        return {
            "type": "student",
            "name": student.character_name if student else "Unknown Student",
            "avatar": student.avatar_path if student else None,
        }
    elif media.posted_by_admin_id:
        admin = User.query.get(media.posted_by_admin_id)
        return {
            "type": "admin",
            "name": f"{admin.first_name} {admin.last_name}" if admin else "Teacher",
            "avatar": getattr(admin, "profile_picture", None) if admin else None,
        }
    else:
        return {
            "type": "unknown",
            "name": "Unknown",
            "avatar": None,
        }


def _get_interaction_info(media):
    """Get interaction counts and current user's interactions."""
    info = {
        "graph_likes": media.graph_likes,
        "eye_likes": media.eye_likes,
        "read_likes": media.read_likes,
        "total_comments": media.comments.count(),
        "user_interactions": None,
    }

    # Get current user's interactions if they're a student
    if not current_user.is_authenticated:
        student_id = session.get("student_id")
        if student_id:
            interaction = StudentMediaInteraction.query.filter_by(
                student_id=student_id, media_id=media.id
            ).first()
            if interaction:
                info["user_interactions"] = {
                    "liked_graph": interaction.liked_graph,
                    "liked_eye": interaction.liked_eye,
                    "liked_read": interaction.liked_read,
                    "comment_count": interaction.comment_count,
                }

    return info


def _increment_comment_count(student_id, media_id):
    """Increment the comment count in StudentMediaInteraction."""
    interaction = StudentMediaInteraction.query.filter_by(
        student_id=student_id, media_id=media_id
    ).first()

    if interaction:
        interaction.comment_count += 1
    else:
        # Create new interaction record
        interaction = StudentMediaInteraction(
            student_id=student_id,
            media_id=media_id,
            comment_count=1,
            liked_graph=False,
            liked_eye=False,
            liked_read=False,
        )
        db.session.add(interaction)

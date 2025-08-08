from functools import wraps

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash

from forms import UserCreationForm
from models.base import db
from models.district import District
from models.school import School
from models.user import User

from .base import create_blueprint

bp = create_blueprint("admin")


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (
            current_user.is_admin() or current_user.is_staff()
        ):
            return render_template("errors/403.html"), 403
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/admin", methods=["GET"])
@login_required
@admin_required
def admin_dashboard():
    form = UserCreationForm()
    users = User.query.order_by(User.created_at.desc()).all()
    schools = School.query.all()
    districts = District.query.all()
    return render_template(
        "admin/dashboard.html",
        form=form,
        roles=User.Role,
        users=users,
        schools=schools,
        districts=districts,
    )


@bp.route("/admin/create_user", methods=["POST"])
@login_required
@admin_required
def create_user():
    if not current_user.is_admin():
        flash("Only administrators can create new users.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    try:
        new_user = User(
            username=request.form["username"],
            email=request.form["email"],
            password_hash=generate_password_hash(request.form["password"]),
            first_name=request.form["first_name"],
            last_name=request.form["last_name"],
            role=User.Role(request.form["role"]),
        )
        new_user.validate()
        db.session.add(new_user)
        db.session.commit()
        flash("User created successfully!", "success")
    except ValueError as e:
        flash(str(e), "danger")
    except Exception:
        flash("Error creating user. Please try again.", "danger")
        db.session.rollback()

    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/admin/edit_user/<int:user_id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == "POST":
        try:
            user.username = request.form["username"]
            user.email = request.form["email"]
            user.first_name = request.form["first_name"]
            user.last_name = request.form["last_name"]

            # Only allow admin to change roles
            if current_user.is_admin():
                user.role = User.Role(request.form["role"])

            if request.form.get("password"):
                user.password_hash = generate_password_hash(request.form["password"])

            # Handle school and district for teachers/observers
            if user.requires_school_info():
                user.school_id = request.form.get("school_id")
                user.district_id = request.form.get("district_id")

            valid, message = user.validate()
            if not valid:
                return jsonify({"success": False, "message": message}), 400

            db.session.commit()
            return jsonify({"success": True, "message": "User updated successfully!"})
        except ValueError as e:
            return jsonify({"success": False, "message": str(e)}), 400
        except Exception:
            db.session.rollback()
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Error updating user. Please try again.",
                    }
                ),
                500,
            )

    # GET request - return user data
    return jsonify(
        {
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value,
            "school_id": user.school_id,
            "district_id": user.district_id,
        }
    )


@bp.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    if not current_user.is_admin():
        return (
            jsonify(
                {"success": False, "message": "Only administrators can delete users"}
            ),
            403,
        )

    if current_user.id == user_id:
        return (
            jsonify({"success": False, "message": "Cannot delete your own account"}),
            400,
        )

    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully!", "success")
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

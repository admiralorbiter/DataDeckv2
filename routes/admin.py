from functools import wraps

from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.security import generate_password_hash

from forms import ModuleForm, UserCreationForm
from models.base import db
from models.district import District
from models.module import Module
from models.observer import Observer
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
    module_form = ModuleForm()
    users = User.query.order_by(User.created_at.desc()).all()
    schools = School.query.all()
    districts = District.query.all()
    modules = Module.query.order_by(Module.sort_order.asc(), Module.name.asc()).all()
    return render_template(
        "admin/dashboard.html",
        form=form,
        module_form=module_form,
        roles=User.Role,
        users=users,
        schools=schools,
        districts=districts,
        modules=modules,
    )


@bp.route("/admin/create_user", methods=["POST"])
@login_required
@admin_required
def create_user():
    if not current_user.is_admin():
        flash("Only administrators can create new users.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    try:
        role_value = request.form["role"]
        is_observer = role_value == User.Role.OBSERVER.value
        base_kwargs = {
            "username": request.form["username"],
            "email": request.form["email"],
            "password_hash": generate_password_hash(request.form["password"]),
            "first_name": request.form["first_name"],
            "last_name": request.form["last_name"],
            "role": User.Role(role_value),
        }

        # Create correct subclass for observer accounts so observer login works
        new_user = Observer(**base_kwargs) if is_observer else User(**base_kwargs)

        # Handle school/district info for teachers/observers (only use IDs now)
        if new_user.requires_school_info():
            school_id_str = request.form.get("school_id", "").strip()
            district_id_str = request.form.get("district_id", "").strip()
            school_name = request.form.get("school", "").strip()
            district_name = request.form.get("district", "").strip()

            # Set school_id (prefer ID, but create school if name provided)
            if school_id_str:
                try:
                    new_user.school_id = int(school_id_str)
                except ValueError:
                    flash("Invalid school ID provided.", "danger")
                    return redirect(url_for("admin.admin_dashboard"))
            elif school_name:
                # Find or create school by name
                school = School.query.filter_by(name=school_name).first()
                if not school:
                    # Need district first for school creation
                    if not district_id_str and not district_name:
                        flash(
                            "District is required when creating a new school.", "danger"
                        )
                        return redirect(url_for("admin.admin_dashboard"))
                    # Will set school after district is resolved
                else:
                    new_user.school_id = school.id

            # Set district_id (prefer ID, but create district if name provided)
            if district_id_str:
                try:
                    new_user.district_id = int(district_id_str)
                except ValueError:
                    flash("Invalid district ID provided.", "danger")
                    return redirect(url_for("admin.admin_dashboard"))
            elif district_name:
                # Find or create district by name
                district = District.query.filter_by(name=district_name).first()
                if not district:
                    district = District(name=district_name)
                    db.session.add(district)
                    db.session.flush()  # Get ID
                new_user.district_id = district.id

                # Now create school if needed
                if school_name and not new_user.school_id:
                    school = School(name=school_name, district_id=district.id)
                    db.session.add(school)
                    db.session.flush()  # Get ID
                    new_user.school_id = school.id
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
                school_id_str = request.form.get("school_id", "").strip()
                district_id_str = request.form.get("district_id", "").strip()

                # Set school_id (convert empty string to None)
                if school_id_str:
                    try:
                        user.school_id = int(school_id_str)
                    except ValueError:
                        return (
                            jsonify({"success": False, "message": "Invalid school ID"}),
                            400,
                        )
                else:
                    user.school_id = None

                # Set district_id (convert empty string to None)
                if district_id_str:
                    try:
                        user.district_id = int(district_id_str)
                    except ValueError:
                        return (
                            jsonify(
                                {"success": False, "message": "Invalid district ID"}
                            ),
                            400,
                        )
                else:
                    user.district_id = None

            # Validate will raise ValueError on failure
            user.validate()

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


# Module Management Routes


@bp.route("/admin/create_module", methods=["POST"])
@login_required
@admin_required
def create_module():
    """Create a new curriculum module."""
    form = ModuleForm()

    if form.validate_on_submit():
        try:
            # Check if module name already exists
            existing_module = Module.query.filter_by(name=form.name.data).first()
            if existing_module:
                flash(f"Module '{form.name.data}' already exists.", "danger")
                return redirect(url_for("admin.admin_dashboard"))

            module = Module(
                name=form.name.data,
                description=form.description.data,
                sort_order=form.sort_order.data,
                is_active=form.is_active.data,
            )

            db.session.add(module)
            db.session.commit()
            flash(f"Module '{module.name}' created successfully!", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating module: {e}", "danger")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{field}: {error}", "danger")

    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/admin/edit_module/<int:module_id>", methods=["POST"])
@login_required
@admin_required
def edit_module(module_id):
    """Edit an existing curriculum module."""
    module = Module.query.get_or_404(module_id)

    try:
        # Check if new name conflicts with existing module (excluding current one)
        new_name = request.form.get("name", "").strip()
        if new_name and new_name != module.name:
            existing_module = Module.query.filter(
                Module.name == new_name, Module.id != module_id
            ).first()
            if existing_module:
                flash(f"Module name '{new_name}' already exists.", "danger")
                return redirect(url_for("admin.admin_dashboard"))

        # Update fields
        if new_name:
            module.name = new_name

        description = request.form.get("description", "").strip()
        module.description = description if description else None

        try:
            sort_order = int(request.form.get("sort_order", 0))
            module.sort_order = max(0, sort_order)  # Ensure non-negative
        except (ValueError, TypeError):
            module.sort_order = 0

        is_active = request.form.get("is_active") == "True"
        module.is_active = is_active

        db.session.commit()
        flash(f"Module '{module.name}' updated successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating module: {e}", "danger")

    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/admin/toggle_module/<int:module_id>", methods=["POST"])
@login_required
@admin_required
def toggle_module(module_id):
    """Toggle module active/inactive status."""
    module = Module.query.get_or_404(module_id)

    try:
        module.is_active = not module.is_active
        db.session.commit()

        status = "activated" if module.is_active else "deactivated"
        flash(f"Module '{module.name}' {status} successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error toggling module status: {e}", "danger")

    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/admin/delete_module/<int:module_id>", methods=["POST"])
@login_required
@admin_required
def delete_module(module_id):
    """Delete a curriculum module (only if no sessions use it)."""
    module = Module.query.get_or_404(module_id)

    try:
        # Check if any sessions use this module
        from models.session import Session

        session_count = Session.query.filter_by(module_id=module_id).count()

        if session_count > 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": (
                            f"Cannot delete module '{module.name}' - "
                            f"it is used by {session_count} session(s)."
                        ),
                    }
                ),
                400,
            )

        module_name = module.name
        db.session.delete(module)
        db.session.commit()

        flash(f"Module '{module_name}' deleted successfully!", "success")
        return jsonify({"success": True})

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

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


# -------------------- District Management --------------------


@bp.route("/admin/districts/create", methods=["POST"])
@login_required
@admin_required
def create_district():
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip() or None
    if not name:
        flash("District name is required.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    try:
        if District.query.filter_by(name=name).first():
            flash(f"District '{name}' already exists.", "danger")
            return redirect(url_for("admin.admin_dashboard"))
        if code and District.query.filter_by(code=code).first():
            flash(f"District code '{code}' already exists.", "danger")
            return redirect(url_for("admin.admin_dashboard"))

        d = District(name=name, code=code)
        db.session.add(d)
        db.session.commit()
        flash(f"District '{name}' created.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating district: {e}", "danger")
    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/admin/districts/<int:district_id>", methods=["GET"])
@login_required
@admin_required
def get_district(district_id: int):
    d = District.query.get_or_404(district_id)
    return jsonify({"id": d.id, "name": d.name, "code": d.code})


@bp.route("/admin/districts/<int:district_id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_district(district_id: int):
    d = District.query.get_or_404(district_id)
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip() or None
    try:
        if name and name != d.name:
            if District.query.filter(
                District.name == name, District.id != d.id
            ).first():
                flash(f"Another district already uses the name '{name}'.", "danger")
                return redirect(url_for("admin.admin_dashboard"))
            d.name = name
        if (code or code is None) and code != d.code:
            if (
                code
                and District.query.filter(
                    District.code == code, District.id != d.id
                ).first()
            ):
                flash(f"Another district already uses the code '{code}'.", "danger")
                return redirect(url_for("admin.admin_dashboard"))
            d.code = code
        db.session.commit()
        flash("District updated successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating district: {e}", "danger")
    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/admin/districts/<int:district_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_district(district_id: int):
    if not current_user.is_admin():
        return (
            jsonify(
                {
                    "success": False,
                    "message": "Only administrators can delete districts",
                }
            ),
            403,
        )
    d = District.query.get_or_404(district_id)
    try:
        if d.schools.count() > 0 or d.users.count() > 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": (
                            "Cannot delete district with schools or users. "
                            "Move or delete them first."
                        ),
                    }
                ),
                400,
            )
        db.session.delete(d)
        db.session.commit()
        flash("District deleted.", "success")
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# -------------------- School Management --------------------


@bp.route("/admin/schools/create", methods=["POST"])
@login_required
@admin_required
def create_school():
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip() or None
    try:
        district_id = int(request.form.get("district_id", "0"))
    except ValueError:
        district_id = 0

    if not name or not district_id:
        flash("School name and district are required.", "danger")
        return redirect(url_for("admin.admin_dashboard"))

    try:
        if code and School.query.filter_by(code=code).first():
            flash(f"School code '{code}' already exists.", "danger")
            return redirect(url_for("admin.admin_dashboard"))

        s = School(name=name, code=code, district_id=district_id)
        db.session.add(s)
        db.session.commit()
        flash(f"School '{name}' created.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error creating school: {e}", "danger")
    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/admin/schools/<int:school_id>", methods=["GET"])
@login_required
@admin_required
def get_school(school_id: int):
    s = School.query.get_or_404(school_id)
    return jsonify(
        {"id": s.id, "name": s.name, "code": s.code, "district_id": s.district_id}
    )


@bp.route("/admin/schools/<int:school_id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_school(school_id: int):
    s = School.query.get_or_404(school_id)
    name = request.form.get("name", "").strip()
    code = request.form.get("code", "").strip() or None
    try:
        district_id = int(request.form.get("district_id", "0"))
    except ValueError:
        district_id = 0

    try:
        if name and name != s.name:
            s.name = name
        if (code or code is None) and code != s.code:
            if (
                code
                and School.query.filter(School.code == code, School.id != s.id).first()
            ):
                flash(f"Another school already uses the code '{code}'.", "danger")
                return redirect(url_for("admin.admin_dashboard"))
            s.code = code
        if district_id and district_id != s.district_id:
            # Ensure district exists
            if not District.query.get(district_id):
                flash("Invalid district.", "danger")
                return redirect(url_for("admin.admin_dashboard"))
            s.district_id = district_id
        db.session.commit()
        flash("School updated successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating school: {e}", "danger")
    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/admin/schools/<int:school_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_school(school_id: int):
    if not current_user.is_admin():
        return (
            jsonify(
                {"success": False, "message": "Only administrators can delete schools"}
            ),
            403,
        )
    s = School.query.get_or_404(school_id)
    try:
        if s.users.count() > 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": (
                            "Cannot delete school with users. "
                            "Reassign or delete users first."
                        ),
                    }
                ),
                400,
            )
        db.session.delete(s)
        db.session.commit()
        flash("School deleted.", "success")
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# -------------------- Observer Management --------------------


@bp.route("/admin/observers/<int:user_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_observer(user_id: int):
    user = User.query.get_or_404(user_id)
    if not isinstance(user, Observer):
        flash("Selected user is not an observer.", "danger")
        return redirect(url_for("admin.admin_dashboard"))
    try:
        user.is_active = not bool(user.is_active)
        db.session.commit()
        status = "activated" if user.is_active else "deactivated"
        flash(f"Observer {status} successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating observer: {e}", "danger")
    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/admin/observers/<int:user_id>/reset-password", methods=["POST"])
@login_required
@admin_required
def reset_observer_password(user_id: int):
    if not current_user.is_admin():
        flash("Only administrators can reset passwords.", "danger")
        return redirect(url_for("admin.admin_dashboard"))
    user = User.query.get_or_404(user_id)
    if not isinstance(user, Observer):
        flash("Selected user is not an observer.", "danger")
        return redirect(url_for("admin.admin_dashboard"))
    new_password = request.form.get("new_password", "").strip()
    if not new_password:
        flash("New password is required.", "danger")
        return redirect(url_for("admin.admin_dashboard"))
    try:
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        flash("Observer password reset successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error resetting password: {e}", "danger")
    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/admin/observers/<int:user_id>/assign-district", methods=["POST"])
@login_required
@admin_required
def assign_observer_district(user_id: int):
    user = User.query.get_or_404(user_id)
    if not isinstance(user, Observer):
        return (
            jsonify({"success": False, "message": "Selected user is not an observer."}),
            400,
        )
    try:
        district_id = int(request.form.get("district_id", "0"))
    except ValueError:
        district_id = 0
    if not district_id:
        return (
            jsonify({"success": False, "message": "District is required."}),
            400,
        )
    try:
        if not District.query.get(district_id):
            return (
                jsonify({"success": False, "message": "Invalid district."}),
                400,
            )
        user.district_id = district_id
        db.session.commit()
        return jsonify({"success": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500


# -------------------- Teacher Reassignment --------------------


@bp.route("/admin/teachers/<int:user_id>/assign", methods=["POST"])
@login_required
@admin_required
def assign_teacher(user_id: int):
    """Assign or reassign a teacher's district and school."""
    user = User.query.get_or_404(user_id)
    if not user.is_teacher():
        return (
            jsonify({"success": False, "message": "Selected user is not a teacher."}),
            400,
        )

    # Parse IDs
    district_id_raw = request.form.get("district_id", "").strip()
    school_id_raw = request.form.get("school_id", "").strip()
    try:
        district_id = int(district_id_raw) if district_id_raw else None
    except ValueError:
        return jsonify({"success": False, "message": "Invalid district id."}), 400
    try:
        school_id = int(school_id_raw) if school_id_raw else None
    except ValueError:
        return jsonify({"success": False, "message": "Invalid school id."}), 400

    # Validate
    if district_id is None:
        return jsonify({"success": False, "message": "District is required."}), 400
    district = District.query.get(district_id)
    if not district:
        return jsonify({"success": False, "message": "District not found."}), 404

    if school_id is not None:
        school = School.query.get(school_id)
        if not school:
            return jsonify({"success": False, "message": "School not found."}), 404
        if school.district_id != district_id:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "School must belong to the selected district.",
                    }
                ),
                400,
            )

    try:
        user.district_id = district_id
        user.school_id = school_id
        user.validate()
        db.session.commit()
        return jsonify({"success": True})
    except ValueError as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": str(e)}), 500

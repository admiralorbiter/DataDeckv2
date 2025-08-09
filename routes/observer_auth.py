from flask import redirect, url_for

from .base import create_blueprint

bp = create_blueprint("observer_auth")


@bp.route("/observer/login", methods=["GET", "POST"])
def observer_login():
    # Legacy route redirects to unified login
    return redirect(url_for("auth.login"))


@bp.route("/observer/logout", methods=["POST", "GET"])
def observer_logout():
    # Legacy route redirects to unified logout
    return redirect(url_for("auth.logout"))

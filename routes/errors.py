"""Error handling routes and templates."""

from flask import jsonify, render_template, request

from .base import create_blueprint

bp = create_blueprint("errors")


@bp.app_errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors."""
    if request.is_json:
        return (
            jsonify(
                {
                    "error": "Forbidden",
                    "message": "You do not have permission to access this resource.",
                    "status_code": 403,
                }
            ),
            403,
        )

    return render_template("errors/403.html"), 403


@bp.app_errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    if request.is_json:
        return (
            jsonify(
                {
                    "error": "Not Found",
                    "message": "The requested resource was not found.",
                    "status_code": 404,
                }
            ),
            404,
        )

    return render_template("errors/404.html"), 404


@bp.app_errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    if request.is_json:
        return (
            jsonify(
                {
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred. Please try again.",
                    "status_code": 500,
                }
            ),
            500,
        )

    return render_template("errors/500.html"), 500

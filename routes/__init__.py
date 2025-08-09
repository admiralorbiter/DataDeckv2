from flask import Flask

from .admin import bp as admin_bp
from .auth import bp as auth_bp
from .errors import bp as errors_bp
from .main import bp as main_bp
from .profile import bp as profile_bp
from .sessions import bp as sessions_bp


def init_app(app: Flask):
    """Initialize all blueprints with the app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(sessions_bp)
    app.register_blueprint(errors_bp)

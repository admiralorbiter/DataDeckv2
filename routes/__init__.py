from flask import Flask
from .auth import bp as auth_bp
from .main import bp as main_bp
from .admin import bp as admin_bp

def init_app(app: Flask):
    """Initialize all blueprints with the app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp) 
import os

from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import DevelopmentConfig, ProductionConfig, TestingConfig
from models import User, db
from routes import init_app as init_routes

# Load environment variables from .env file as early as possible
load_dotenv()

# Extensions (initialized without app; bound in create_app)
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name: str | None = None) -> Flask:
    """Application factory for DataDeck v2."""
    app = Flask(__name__)

    # Select config
    env = (config_name or os.environ.get("FLASK_ENV", "development")).lower()
    if env == "production":
        app.config.from_object(ProductionConfig)
    elif env == "testing" or env == "test":
        app.config.from_object(TestingConfig)
    else:
        app.config.from_object(DevelopmentConfig)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Flask-Login settings
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # User loader callback for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints/routes
    init_routes(app)

    # Custom Jinja filters
    @app.template_filter("nl2br")
    def nl2br_filter(text):
        """Convert newlines to HTML line breaks."""
        if not text:
            return text
        return text.replace("\n", "<br>\n")

    # Template context processors
    @app.context_processor
    def inject_nav_sessions():
        """Make nav session helper available to all templates."""
        try:
            from services.nav_sessions import get_nav_sessions_for_current_user

            nav_sessions = get_nav_sessions_for_current_user()
            return {"nav_sessions": nav_sessions}
        except Exception:
            # Graceful fallback if helper fails
            return {"nav_sessions": {"type": "none", "data": None}}

    # Create DB schema on startup (no Alembic in current phase)
    with app.app_context():
        db.create_all()

    return app


# Create a default app instance for scripts and `python app.py`
app = create_app()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

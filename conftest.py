import pytest

from app import create_app
from config import TestingConfig
from models import db


@pytest.fixture
def app():
    test_app = create_app("testing")
    # Ensure testing config is applied (factory does this for 'testing')
    test_app.config.from_object(TestingConfig)

    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()

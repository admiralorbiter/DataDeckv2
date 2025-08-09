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


# Student Management Test Fixtures (M4)
@pytest.fixture
def teacher_user(app):
    """Create a teacher user for testing."""
    from tests.factories import create_district, create_school, create_teacher

    district = create_district("Test District")
    school = create_school(district, "Test School")
    teacher = create_teacher(district, school, "test_teacher")
    db.session.commit()
    return teacher


@pytest.fixture
def observer_user(app):
    """Create an observer user for testing."""
    from werkzeug.security import generate_password_hash

    from models import User

    observer = User(
        username="test_observer",
        email="observer@test.com",
        password_hash=generate_password_hash("password123"),
        role=User.Role.OBSERVER,
    )
    db.session.add(observer)
    db.session.commit()
    return observer


@pytest.fixture
def student_factory(app):
    """Factory for creating students."""

    def _create_student(**kwargs):
        from models import User
        from tests.factories import create_module, create_session, create_student

        # Get or create teacher
        teacher_id = kwargs.get("teacher_id")
        if teacher_id:
            teacher = User.query.get(teacher_id)
        else:
            from tests.factories import create_district, create_school, create_teacher

            district = create_district()
            school = create_school(district)
            teacher = create_teacher(district, school)
            teacher_id = teacher.id

        # Get or create session
        section_id = kwargs.get("section_id")
        if section_id:
            from models import Session

            session = Session.query.get(section_id)
        else:
            module = create_module()
            session = create_session(teacher, module=module)

        student = create_student(teacher, session)

        # Override any provided attributes
        for key, value in kwargs.items():
            if hasattr(student, key):
                setattr(student, key, value)

        db.session.commit()
        return student

    return _create_student


@pytest.fixture
def session_factory(app):
    """Factory for creating sessions."""

    def _create_session(**kwargs):
        from models import User
        from tests.factories import create_module, create_session

        created_by_id = kwargs.get("created_by_id")
        if created_by_id:
            teacher = User.query.get(created_by_id)
        else:
            from tests.factories import create_district, create_school, create_teacher

            district = create_district()
            school = create_school(district)
            teacher = create_teacher(district, school)

        module = create_module()
        session = create_session(teacher, module=module)

        # Override any provided attributes
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)

        db.session.commit()
        return session

    return _create_session


@pytest.fixture
def teacher_factory(app):
    """Factory for creating teachers."""

    def _create_teacher(**kwargs):
        from tests.factories import create_district, create_school, create_teacher

        district = create_district()
        school = create_school(district)
        teacher = create_teacher(district, school)

        # Override any provided attributes
        for key, value in kwargs.items():
            if hasattr(teacher, key):
                setattr(teacher, key, value)

        db.session.commit()
        return teacher

    return _create_teacher


@pytest.fixture
def session_with_students(app, teacher_user):
    """Create a session with multiple students for testing."""
    from tests.factories import create_module, create_session, create_student

    module = create_module("Test Module")
    session = create_session(teacher_user, section=1, module=module)

    # Create 3 students for the session
    students = []
    for i in range(3):
        student = create_student(teacher_user, session)
        students.append(student)

    db.session.commit()
    session.test_students = students  # Attach for easy access in tests
    return session

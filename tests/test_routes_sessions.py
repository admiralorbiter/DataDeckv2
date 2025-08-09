"""Tests for session routes and functionality."""

import pytest
from werkzeug.security import generate_password_hash

from models import District, Module, School, Session, User, db


@pytest.fixture
def teacher(app):
    """Create a teacher with proper school/district relationships."""
    with app.app_context():
        district = District(name="Test District")
        db.session.add(district)
        db.session.flush()

        school = School(name="Test School", district_id=district.id)
        db.session.add(school)
        db.session.flush()

        teacher = User(
            username="test_teacher",
            email="teacher@test.com",
            password_hash=generate_password_hash("password"),
            role=User.Role.TEACHER,
            school_id=school.id,
            district_id=district.id,
        )
        db.session.add(teacher)
        db.session.commit()
        yield teacher


@pytest.fixture
def admin_user(app):
    """Create an admin user."""
    with app.app_context():
        admin = User(
            username="admin",
            email="admin@test.com",
            password_hash=generate_password_hash("password"),
            role=User.Role.ADMIN,
        )
        db.session.add(admin)
        db.session.commit()
        yield admin


@pytest.fixture
def student_user(app):
    """Create a student user."""
    with app.app_context():
        student = User(
            username="student",
            email="student@test.com",
            password_hash=generate_password_hash("password"),
            role=User.Role.STUDENT,
        )
        db.session.add(student)
        db.session.commit()
        yield student


@pytest.fixture
def test_module(app):
    """Create a test module."""
    with app.app_context():
        module = Module(
            name="Test Module",
            description="A test module for sessions",
            is_active=True,
            sort_order=1,
        )
        db.session.add(module)
        db.session.commit()
        yield module


@pytest.fixture
def existing_session(app, teacher, test_module):
    """Create an existing session for conflict testing."""
    with app.app_context():
        session = Session(
            name="Existing Session",
            section=1,
            module_id=test_module.id,
            session_code="EXIST123",
            created_by_id=teacher.id,
            character_set="animals",
        )
        db.session.add(session)
        db.session.commit()
        yield session


class TestSessionsRoutes:
    """Test session route functionality."""

    def test_start_session_requires_login(self, client):
        """Test that starting a session requires login."""
        response = client.get("/sessions/start")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_start_session_requires_teacher_role(self, client, student_user):
        """Test that only teachers/admins can start sessions."""
        # Login as student
        response = client.post(
            "/login",
            data={
                "username": student_user.email,
                "password": "password",
                "csrf_token": "test",
            },
            follow_redirects=True,
        )

        # Try to access session start - should redirect to main page
        response = client.get("/sessions/start", follow_redirects=False)
        assert response.status_code == 302
        assert "/main" in response.location or "/" in response.location

        # Follow redirect and check that we're redirected away from sessions
        response = client.get("/sessions/start", follow_redirects=True)
        assert response.status_code == 200
        # Should be on the main page, not the sessions page
        assert b"Data Deck" in response.data or b"index" in response.data.lower()

    def test_start_session_get_renders_form(self, client, teacher):
        """Test that GET request renders the session start form."""
        # Login as teacher
        client.post(
            "/login",
            data={
                "username": teacher.email,
                "password": "password",
                "csrf_token": "test",
            },
        )

        response = client.get("/sessions/start")
        assert response.status_code == 200
        assert (
            b"Start New Session" in response.data
            or b"Create Session" in response.data
            or b"session" in response.data.lower()
        )

    def test_start_session_successful_creation(self, client, teacher, test_module):
        """Test successful session creation."""
        # Login as teacher
        client.post(
            "/login",
            data={
                "username": teacher.email,
                "password": "password",
                "csrf_token": "test",
            },
        )

        response = client.post(
            "/sessions/start",
            data={
                "name": "Test Session",
                "section": "2",
                "module": str(test_module.id),
                "character_set": "animals",
                "csrf_token": "test",  # CSRF disabled in tests
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Check that session was created
        session = Session.query.filter_by(name="Test Session").first()
        assert session is not None
        assert session.section == 2
        assert session.created_by_id == teacher.id
        assert session.module_id == test_module.id

    def test_start_session_conflict_detection(
        self, client, teacher, test_module, existing_session
    ):
        """Test that session conflicts are detected."""
        # Login as teacher
        client.post(
            "/login",
            data={
                "username": teacher.email,
                "password": "password",
                "csrf_token": "test",
            },
        )

        response = client.post(
            "/sessions/start",
            data={
                "name": "Conflicting Session",
                "section": "1",  # Same section as existing_session
                "module": str(test_module.id),
                "character_set": "animals",
                "csrf_token": "test",
            },
        )

        assert response.status_code == 200
        # Should show conflict resolution options
        assert (
            b"conflict" in response.data.lower() or b"existing" in response.data.lower()
        )

    def test_start_session_auto_archive(
        self, client, teacher, test_module, existing_session
    ):
        """Test auto-archiving existing sessions."""
        # Login as teacher
        client.post(
            "/login",
            data={
                "username": teacher.email,
                "password": "password",
                "csrf_token": "test",
            },
        )

        response = client.post(
            "/sessions/start",
            data={
                "name": "New Session",
                "section": "1",  # Same section as existing_session
                "module": str(test_module.id),
                "character_set": "animals",
                "archive_and_create": "true",
                "csrf_token": "test",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Check that old session is archived
        db.session.refresh(existing_session)
        assert existing_session.is_archived is True

        # Check that new session was created
        new_session = Session.query.filter_by(name="New Session").first()
        assert new_session is not None
        assert new_session.is_archived is False

    def test_sessions_list_requires_login(self, client):
        """Test that sessions list requires login."""
        response = client.get("/sessions")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_sessions_list_shows_user_sessions(self, client, teacher, existing_session):
        """Test that sessions list shows user's sessions."""
        # Login as teacher
        client.post(
            "/login",
            data={
                "username": teacher.email,
                "password": "password",
                "csrf_token": "test",
            },
        )

        response = client.get("/sessions")
        assert response.status_code == 200
        assert existing_session.name.encode() in response.data

    def test_session_detail_requires_login(self, client, existing_session):
        """Test that session detail requires login."""
        response = client.get(f"/sessions/{existing_session.id}")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_session_detail_shows_session_info(self, client, teacher, existing_session):
        """Test that session detail shows session information."""
        # Login as teacher
        client.post(
            "/login",
            data={
                "username": teacher.email,
                "password": "password",
                "csrf_token": "test",
            },
        )

        response = client.get(f"/sessions/{existing_session.id}")
        assert response.status_code == 200
        assert existing_session.name.encode() in response.data
        assert str(existing_session.section).encode() in response.data

    def test_session_archive_requires_login(self, client, existing_session):
        """Test that session archive requires login."""
        response = client.post(f"/sessions/{existing_session.id}/archive")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_session_archive_success(self, client, teacher, existing_session):
        """Test successful session archiving."""
        # Login as teacher
        client.post(
            "/login",
            data={
                "username": teacher.email,
                "password": "password",
                "csrf_token": "test",
            },
        )

        response = client.post(
            f"/sessions/{existing_session.id}/archive",
            data={"csrf_token": "test"},
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Check that session is archived
        db.session.refresh(existing_session)
        assert existing_session.is_archived is True
        assert existing_session.archived_at is not None

    def test_session_unarchive_success(self, client, teacher, existing_session):
        """Test successful session unarchiving."""
        # First archive the session
        existing_session.archive()
        db.session.commit()

        # Login as teacher
        client.post(
            "/login",
            data={
                "username": teacher.email,
                "password": "password",
                "csrf_token": "test",
            },
        )

        response = client.post(
            f"/sessions/{existing_session.id}/unarchive",
            data={"csrf_token": "test"},
            follow_redirects=True,
        )

        assert response.status_code == 200

        # Check that session is unarchived
        db.session.refresh(existing_session)
        assert existing_session.is_archived is False
        assert existing_session.archived_at is None

    def test_session_access_control(
        self, client, teacher, admin_user, existing_session
    ):
        """Test that users can only access their own sessions (except admins)."""
        # Create another teacher
        other_teacher = User(
            username="other_teacher",
            email="other@test.com",
            password_hash=generate_password_hash("password"),
            role=User.Role.TEACHER,
            school_id=teacher.school_id,
            district_id=teacher.district_id,
        )
        db.session.add(other_teacher)
        db.session.commit()

        # Other teacher should be redirected when trying to access session
        # Login as other teacher
        client.post(
            "/login",
            data={
                "username": other_teacher.email,
                "password": "password",
                "csrf_token": "test",
            },
        )

        response = client.get(
            f"/sessions/{existing_session.id}", follow_redirects=False
        )
        assert response.status_code == 302  # Redirected away from session
        assert "/sessions" in response.location  # Redirected to sessions list

        # Admin should be able to access any session
        # Login as admin
        client.post(
            "/login",
            data={
                "username": admin_user.email,
                "password": "password",
                "csrf_token": "test",
            },
        )

        response = client.get(f"/sessions/{existing_session.id}")
        assert response.status_code == 200


class TestSessionsIntegration:
    """Integration tests for session functionality."""

    def test_complete_session_workflow(self, client, teacher, test_module):
        """Test complete session creation and management workflow."""
        # Login as teacher
        client.post(
            "/login",
            data={
                "username": teacher.email,
                "password": "password",
                "csrf_token": "test",
            },
        )

        # 1. Create a session
        response = client.post(
            "/sessions/start",
            data={
                "name": "Integration Test Session",
                "section": "3",
                "module": str(test_module.id),
                "character_set": "superheroes",
                "csrf_token": "test",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200

        session = Session.query.filter_by(name="Integration Test Session").first()
        assert session is not None

        # 2. Check that students were generated
        students = session.students.all()
        assert len(students) == 20

        # 3. View session list
        response = client.get("/sessions")
        assert b"Integration Test Session" in response.data

        # 4. View session detail
        response = client.get(f"/sessions/{session.id}")
        assert response.status_code == 200
        assert b"Integration Test Session" in response.data

        # 5. Archive the session
        response = client.post(
            f"/sessions/{session.id}/archive",
            data={"csrf_token": "test"},
            follow_redirects=True,
        )
        assert response.status_code == 200

        # 6. Verify session is archived
        db.session.refresh(session)
        assert session.is_archived is True

        # 7. Unarchive the session
        response = client.post(
            f"/sessions/{session.id}/unarchive",
            data={"csrf_token": "test"},
            follow_redirects=True,
        )
        assert response.status_code == 200

        # 8. Verify session is unarchived
        db.session.refresh(session)
        assert session.is_archived is False

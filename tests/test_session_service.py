import pytest
from werkzeug.security import generate_password_hash

from models import Module, Session, User, db
from services.session_service import SessionConflictError, SessionService


@pytest.fixture
def teacher(app):
    with app.app_context():
        # Create district and school first
        from models import District, School

        district = District(name="Test District")
        db.session.add(district)
        db.session.flush()

        school = School(name="Test School", district_id=district.id)
        db.session.add(school)
        db.session.flush()

        teacher = User(
            username="teacher_test",
            email="teacher_test@example.com",
            password_hash=generate_password_hash("password"),
            role=User.Role.TEACHER,
            school_id=school.id,
            district_id=district.id,
        )
        db.session.add(teacher)
        db.session.commit()
        yield teacher


@pytest.fixture
def module(app):
    with app.app_context():
        module = Module(
            name="Test Module",
            description="A test curriculum module",
            is_active=True,
            sort_order=1,
        )
        db.session.add(module)
        db.session.commit()
        yield module


def test_session_uniqueness_validation_no_conflict(app, teacher, module):
    """Test that validation passes when no conflicting session exists."""
    with app.app_context():
        # Should return None (no conflict) for section 1
        conflict = SessionService.validate_session_uniqueness(teacher.id, 1)
        assert conflict is None


def test_session_uniqueness_validation_with_conflict(app, teacher, module):
    """Test that validation detects conflicting active sessions."""
    with app.app_context():
        # Create an active session for section 1
        existing = Session(
            name="Existing Session",
            section=1,
            module_id=module.id,
            session_code="ABCD1234",
            created_by_id=teacher.id,
            character_set="animals",
        )
        db.session.add(existing)
        db.session.commit()

        # Should detect conflict for same section
        conflict = SessionService.validate_session_uniqueness(teacher.id, 1)
        assert conflict is not None
        assert conflict.id == existing.id

        # Should not detect conflict for different section
        conflict = SessionService.validate_session_uniqueness(teacher.id, 2)
        assert conflict is None


def test_session_uniqueness_ignores_archived(app, teacher, module):
    """Test that archived sessions don't cause conflicts."""
    with app.app_context():
        # Create an archived session for section 1
        archived = Session(
            name="Archived Session",
            section=1,
            module_id=module.id,
            session_code="ARCH1234",
            created_by_id=teacher.id,
            character_set="animals",
            is_archived=True,
        )
        db.session.add(archived)
        db.session.commit()

        # Should not detect conflict for archived session
        conflict = SessionService.validate_session_uniqueness(teacher.id, 1)
        assert conflict is None


def test_create_session_without_conflict(app, teacher, module):
    """Test creating a session when no conflicts exist."""
    with app.app_context():
        session, was_archived = SessionService.create_session(
            teacher=teacher,
            name="New Session",
            section=1,
            module_id=module.id,
            character_set="animals",
        )

        assert session is not None
        assert session.name == "New Session"
        assert session.section == 1
        assert session.module_id == module.id
        assert session.created_by_id == teacher.id
        assert not was_archived
        assert len(session.session_code) == 8


def test_create_session_with_conflict_raises_error(app, teacher, module):
    """Test that creating a conflicting session raises an error by default."""
    with app.app_context():
        # Create existing session
        existing = Session(
            name="Existing Session",
            section=1,
            module_id=module.id,
            session_code="EXIST123",
            created_by_id=teacher.id,
            character_set="animals",
        )
        db.session.add(existing)
        db.session.commit()

        # Attempting to create conflicting session should raise error
        with pytest.raises(SessionConflictError) as exc_info:
            SessionService.create_session(
                teacher=teacher,
                name="Conflicting Session",
                section=1,
                module_id=module.id,  # Different module, same section
                character_set="superheroes",
            )

        assert exc_info.value.existing_session.id == existing.id


def test_create_session_with_auto_archive(app, teacher, module):
    """Test creating a session with auto-archive of conflicting session."""
    with app.app_context():
        # Create existing session
        existing = Session(
            name="Existing Session",
            section=1,
            module_id=module.id,
            session_code="EXIST123",
            created_by_id=teacher.id,
            character_set="animals",
        )
        db.session.add(existing)
        db.session.commit()

        # Create new session with auto-archive
        new_session, was_archived = SessionService.create_session(
            teacher=teacher,
            name="New Session",
            section=1,
            module_id=module.id,
            character_set="superheroes",
            auto_archive_existing=True,
        )

        assert new_session is not None
        assert new_session.name == "New Session"
        assert was_archived

        # Refresh existing session and check it's archived
        db.session.refresh(existing)
        assert existing.is_archived
        assert existing.archived_at is not None


def test_generate_unique_session_code(app, module):
    """Test that session code generation creates unique codes."""
    with app.app_context():
        # Create a session with a specific code
        existing = Session(
            name="Test Session",
            section=1,
            module_id=module.id,
            session_code="TESTCODE",
            created_by_id=1,
            character_set="animals",
        )
        db.session.add(existing)
        db.session.commit()

        # Generate new code should be different
        new_code = SessionService.generate_session_code()
        assert new_code != "TESTCODE"
        assert len(new_code) == 8


def test_generate_students_for_session(app, teacher, module):
    """Test student generation for a session."""
    with app.app_context():
        # Create a session
        session = Session(
            name="Test Session",
            section=1,
            module_id=module.id,
            session_code="STUDENTS",
            created_by_id=teacher.id,
            character_set="animals",
        )
        db.session.add(session)
        db.session.flush()

        # Generate students
        students = SessionService.generate_students_for_session(session, count=5)

        assert len(students) == 5
        assert all(student.teacher_id == teacher.id for student in students)
        assert all(student.section_id == session.id for student in students)
        assert all(
            student.character_name.startswith(
                (
                    "Bear",
                    "Wolf",
                    "Eagle",
                    "Lion",
                    "Tiger",
                    "Shark",
                    "Hawk",
                    "Fox",
                    "Deer",
                    "Owl",
                )
            )
            for student in students
        )

        # Check uniqueness
        names = [s.character_name for s in students]
        assert len(names) == len(set(names))  # All names unique

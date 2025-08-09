import pytest
from werkzeug.security import generate_password_hash

from models import District, School, User, db


@pytest.fixture
def admin_user(app):
    with app.app_context():
        admin = User(
            username="admin_test",
            email="admin_test@example.com",
            password_hash=generate_password_hash("password"),
            role=User.Role.ADMIN,
        )
        db.session.add(admin)
        db.session.commit()
        yield admin


@pytest.fixture
def test_district_and_school(app):
    with app.app_context():
        district = District(name="Test District", code="TD01")
        db.session.add(district)
        db.session.flush()

        school = School(name="Test School", code="TS01", district_id=district.id)
        db.session.add(school)
        db.session.commit()

        yield district, school


def test_create_teacher_with_school_id(
    app, client, admin_user, test_district_and_school
):
    """Test creating a teacher with school and district IDs."""
    district, school = test_district_and_school

    with app.app_context():
        # Login as admin
        client.post(
            "/login",
            data={"username": "admin_test@example.com", "password": "password"},
        )

        # Create teacher with school/district IDs
        response = client.post(
            "/admin/create_user",
            data={
                "username": "teacher_test",
                "email": "teacher_test@example.com",
                "password": "password123",
                "first_name": "Test",
                "last_name": "Teacher",
                "role": "teacher",
                "school_id": str(school.id),
                "district_id": str(district.id),
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"User created successfully!" in response.data

        # Verify user was created correctly
        teacher = User.query.filter_by(username="teacher_test").first()
        assert teacher is not None
        assert teacher.role == User.Role.TEACHER
        assert teacher.school_id == school.id
        assert teacher.district_id == district.id


def test_create_teacher_with_school_names(app, client, admin_user):
    """Test creating a teacher with school and district names (no IDs)."""
    with app.app_context():
        # Login as admin
        client.post(
            "/login",
            data={"username": "admin_test@example.com", "password": "password"},
        )

        # Create teacher with school/district names only
        response = client.post(
            "/admin/create_user",
            data={
                "username": "teacher_names",
                "email": "teacher_names@example.com",
                "password": "password123",
                "first_name": "Names",
                "last_name": "Teacher",
                "role": "teacher",
                "school": "My School",
                "district": "My District",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"User created successfully!" in response.data

        # Verify user was created correctly
        teacher = User.query.filter_by(username="teacher_names").first()
        assert teacher is not None
        assert teacher.role == User.Role.TEACHER
        assert teacher.school.name == "My School"
        assert teacher.district.name == "My District"
        assert teacher.school_id is not None  # Should be set from created school
        assert teacher.district_id is not None  # Should be set from created district


def test_create_teacher_without_school_info_fails(app, client, admin_user):
    """Test that creating a teacher without school/district info fails validation."""
    with app.app_context():
        # Login as admin
        client.post(
            "/login",
            data={"username": "admin_test@example.com", "password": "password"},
        )

        # Try to create teacher without school/district info
        response = client.post(
            "/admin/create_user",
            data={
                "username": "teacher_fail",
                "email": "teacher_fail@example.com",
                "password": "password123",
                "first_name": "Fail",
                "last_name": "Teacher",
                "role": "teacher",
                # No school or district info
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert (
            b"Teachers and Observers must have both school and district assigned"
            in response.data
        )

        # Verify user was NOT created
        teacher = User.query.filter_by(username="teacher_fail").first()
        assert teacher is None


def test_create_student_without_school_info_succeeds(app, client, admin_user):
    """Test that creating a student without school/district info succeeds."""
    with app.app_context():
        # Login as admin
        client.post(
            "/login",
            data={"username": "admin_test@example.com", "password": "password"},
        )

        # Create student without school/district info (should work)
        response = client.post(
            "/admin/create_user",
            data={
                "username": "student_test",
                "email": "student_test@example.com",
                "password": "password123",
                "first_name": "Test",
                "last_name": "Student",
                "role": "student",
                # No school or district info - should be fine for students
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"User created successfully!" in response.data

        # Verify user was created correctly
        student = User.query.filter_by(username="student_test").first()
        assert student is not None
        assert student.role == User.Role.STUDENT
        assert student.school_id is None
        assert student.district_id is None


def test_create_teacher_with_empty_string_ids(app, client, admin_user):
    """Test that empty string IDs are handled properly (converted to None)."""
    with app.app_context():
        # Login as admin
        client.post(
            "/login",
            data={"username": "admin_test@example.com", "password": "password"},
        )

        # Create teacher with empty string IDs but valid names
        response = client.post(
            "/admin/create_user",
            data={
                "username": "teacher_empty",
                "email": "teacher_empty@example.com",
                "password": "password123",
                "first_name": "Empty",
                "last_name": "Teacher",
                "role": "teacher",
                "school_id": "",  # Empty string
                "district_id": "",  # Empty string
                "school": "Empty School",  # Should use these instead
                "district": "Empty District",
            },
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"User created successfully!" in response.data

        # Verify user was created with relationships from names
        teacher = User.query.filter_by(username="teacher_empty").first()
        assert teacher is not None
        assert teacher.school.name == "Empty School"
        assert teacher.district.name == "Empty District"
        assert teacher.school_id is not None  # Should be set from created school
        assert teacher.district_id is not None  # Should be set from created district

import pytest
from datetime import datetime, timezone
from models import User, db
from models.student import Student

@pytest.fixture
def test_user():
    user = User(
        username='testuser',
        email='test@example.com',
        password_hash='fakehash123',
        first_name='Test',
        last_name='User',
        role=User.Role.STUDENT
    )
    return user

@pytest.fixture
def test_teacher():
    teacher = User(
        username='teacher',
        email='teacher@school.com',
        password_hash='fakehash123',
        first_name='Test',
        last_name='Teacher',
        role=User.Role.TEACHER,
        school='Test School',
        district='Test District'
    )
    return teacher

def test_new_user(test_user):
    """Test creating a new user"""
    assert test_user.username == 'testuser'
    assert test_user.email == 'test@example.com'
    assert test_user.password_hash == 'fakehash123'
    assert test_user.first_name == 'Test'
    assert test_user.last_name == 'User'
    assert test_user.role == User.Role.STUDENT

def test_teacher_requires_school_info(test_teacher):
    """Test that teachers require school and district info"""
    assert test_teacher.requires_school_info() is True
    assert test_teacher.school == 'Test School'
    assert test_teacher.district == 'Test District'
    test_teacher.validate()  # Should not raise an error

def test_teacher_validation_fails_without_school():
    """Test that validation fails for teachers without school info"""
    teacher = User(
        username='teacher2',
        email='teacher2@school.com',
        password_hash='fakehash123',
        role=User.Role.TEACHER
    )
    with pytest.raises(ValueError):
        teacher.validate()

def test_student_doesnt_require_school_info(test_user):
    """Test that students don't require school info"""
    assert test_user.requires_school_info() is False
    test_user.validate()  # Should not raise an error

def test_user_roles():
    """Test user role assignments and checks"""
    admin = User(username='admin', role=User.Role.ADMIN)
    teacher = User(
        username='teacher',
        role=User.Role.TEACHER,
        school='School',
        district='District'
    )
    student = User(username='student', role=User.Role.STUDENT)

    assert admin.is_admin() is True
    assert teacher.is_teacher() is True
    assert student.is_student() is True
    assert student.is_admin() is False

def test_user_unique_constraints(test_user, app):
    """Test that unique constraints are enforced"""
    with app.app_context():
        db.session.add(test_user)
        db.session.commit()

        # Try to create another user with the same username
        duplicate_username = User(
            username='testuser',  # Same username
            email='different@example.com',
            password_hash='fakehash456'
        )

        with pytest.raises(Exception):  # SQLAlchemy will raise an error
            db.session.add(duplicate_username)
            db.session.commit()

        db.session.rollback()

        # Try to create another user with the same email
        duplicate_email = User(
            username='different',
            email='test@example.com',  # Same email
            password_hash='fakehash789'
        )

        with pytest.raises(Exception):
            db.session.add(duplicate_email)
            db.session.commit()

def test_student_creation():
    """Test creating a student with character details"""
    teacher = User(
        username='teacher1',
        email='teacher1@school.com',
        password_hash='fakehash123',
        role=User.Role.TEACHER
    )
    
    student = Student(
        username='student1',
        email='student1@school.com',
        password_hash='fakehash456',
        character_name='Warrior123',
        teacher_id=teacher.id,
        character_description='A brave warrior',
        avatar_path='/avatars/warrior.png'
    )
    
    assert student.character_name == 'Warrior123'
    assert student.teacher_id == teacher.id
    assert student.role == User.Role.STUDENT
    assert student.type == 'student'

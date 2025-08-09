"""Tests for School/District relationship models after pure normalization."""

import pytest
from werkzeug.security import generate_password_hash

from models import District, School, User, db


class TestDistrictModel:
    """Test District model functionality."""

    def test_district_creation(self, app):
        """Test basic district creation."""
        with app.app_context():
            district = District(name="Test District", code="TD001")
            db.session.add(district)
            db.session.commit()

            assert district.id is not None
            assert district.name == "Test District"
            assert district.code == "TD001"

    def test_district_name_required(self, app):
        """Test that district name is required."""
        with app.app_context():
            district = District(code="TD001")  # Missing name
            db.session.add(district)

            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()

    def test_district_name_unique(self, app):
        """Test that district names must be unique."""
        with app.app_context():
            district1 = District(name="Unique District")
            district2 = District(name="Unique District")  # Same name

            db.session.add(district1)
            db.session.commit()

            db.session.add(district2)
            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()

    def test_district_code_unique(self, app):
        """Test that district codes must be unique when provided."""
        with app.app_context():
            district1 = District(name="District One", code="SAME")
            district2 = District(name="District Two", code="SAME")  # Same code

            db.session.add(district1)
            db.session.commit()

            db.session.add(district2)
            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()

    def test_district_code_optional(self, app):
        """Test that district code is optional."""
        with app.app_context():
            district = District(name="No Code District")
            db.session.add(district)
            db.session.commit()

            assert district.code is None

    def test_district_repr(self, app):
        """Test district string representation."""
        with app.app_context():
            district = District(name="Test District")
            assert "Test District" in repr(district)


class TestSchoolModel:
    """Test School model functionality."""

    def test_school_creation(self, app):
        """Test basic school creation with district relationship."""
        with app.app_context():
            district = District(name="Test District")
            db.session.add(district)
            db.session.flush()  # Get district ID

            school = School(name="Test School", code="TS001", district_id=district.id)
            db.session.add(school)
            db.session.commit()

            assert school.id is not None
            assert school.name == "Test School"
            assert school.code == "TS001"
            assert school.district_id == district.id

    def test_school_district_relationship(self, app):
        """Test school-district relationship."""
        with app.app_context():
            district = District(name="Parent District")
            db.session.add(district)
            db.session.flush()

            school = School(name="Child School", district_id=district.id)
            db.session.add(school)
            db.session.commit()

            # Test forward relationship
            assert school.district == district
            assert school.district.name == "Parent District"

            # Test backward relationship
            schools = district.schools.all()
            assert school in schools

    def test_school_requires_district(self, app):
        """Test that school requires a district."""
        with app.app_context():
            school = School(name="Orphan School")  # No district_id
            db.session.add(school)

            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()

    def test_school_name_required(self, app):
        """Test that school name is required."""
        with app.app_context():
            district = District(name="Test District")
            db.session.add(district)
            db.session.flush()

            school = School(district_id=district.id)  # Missing name
            db.session.add(school)

            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()

    def test_school_code_unique(self, app):
        """Test that school codes must be unique when provided."""
        with app.app_context():
            district = District(name="Test District")
            db.session.add(district)
            db.session.flush()

            school1 = School(name="School One", code="SAME", district_id=district.id)
            school2 = School(name="School Two", code="SAME", district_id=district.id)

            db.session.add(school1)
            db.session.commit()

            db.session.add(school2)
            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()

    def test_school_code_optional(self, app):
        """Test that school code is optional."""
        with app.app_context():
            district = District(name="Test District")
            db.session.add(district)
            db.session.flush()

            school = School(name="No Code School", district_id=district.id)
            db.session.add(school)
            db.session.commit()

            assert school.code is None

    def test_school_repr(self, app):
        """Test school string representation."""
        with app.app_context():
            district = District(name="Test District")
            db.session.add(district)
            db.session.flush()

            school = School(name="Test School", district_id=district.id)
            assert "Test School" in repr(school)


class TestUserSchoolDistrictRelationships:
    """Test User relationships with School and District."""

    def test_user_school_district_relationships(self, app):
        """Test user relationships with school and district."""
        with app.app_context():
            # Create district and school
            district = District(name="User District")
            db.session.add(district)
            db.session.flush()

            school = School(name="User School", district_id=district.id)
            db.session.add(school)
            db.session.flush()

            # Create user with school and district
            user = User(
                username="test_teacher",
                email="teacher@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.TEACHER,
                school_id=school.id,
                district_id=district.id,
            )
            db.session.add(user)
            db.session.commit()

            # Test forward relationships
            assert user.school == school
            assert user.district == district
            assert user.school.name == "User School"
            assert user.district.name == "User District"

            # Test backward relationships
            assert user in school.users.all()
            assert user in district.users.all()

    def test_teacher_requires_school_district(self, app):
        """Test that teachers require both school and district."""
        with app.app_context():
            district = District(name="Test District")
            db.session.add(district)
            db.session.flush()  # Get district ID first

            school = School(name="Test School", district_id=district.id)
            db.session.add(school)
            db.session.flush()  # Get school ID

            # Teacher without school/district should fail validation
            teacher_no_school = User(
                username="teacher1",
                email="teacher1@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.TEACHER,
                # Missing school_id and district_id
            )

            with pytest.raises(
                ValueError,
                match="Teachers and Observers must have both school and district",
            ):
                teacher_no_school.validate()

            # Teacher with only school should fail validation
            teacher_no_district = User(
                username="teacher2",
                email="teacher2@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.TEACHER,
                school_id=school.id,
                # Missing district_id
            )

            with pytest.raises(
                ValueError,
                match="Teachers and Observers must have both school and district",
            ):
                teacher_no_district.validate()

            # Teacher with both should pass validation
            teacher_complete = User(
                username="teacher3",
                email="teacher3@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.TEACHER,
                school_id=school.id,
                district_id=district.id,
            )

            teacher_complete.validate()  # Should not raise

    def test_observer_requires_school_district(self, app):
        """Test that observers require both school and district."""
        with app.app_context():
            district = District(name="Test District")
            db.session.add(district)
            db.session.flush()  # Get district ID first

            school = School(name="Test School", district_id=district.id)
            db.session.add(school)
            db.session.flush()  # Get school ID

            # Observer without school/district should fail validation
            observer = User(
                username="observer",
                email="observer@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.OBSERVER,
                # Missing school_id and district_id
            )

            with pytest.raises(
                ValueError,
                match="Teachers and Observers must have both school and district",
            ):
                observer.validate()

    def test_admin_student_no_school_district_required(self, app):
        """Test that admins and students don't require school/district."""
        with app.app_context():
            # Admin without school/district should pass validation
            admin = User(
                username="admin",
                email="admin@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.ADMIN,
                # No school_id or district_id
            )
            admin.validate()  # Should not raise

            # Student without school/district should pass validation
            student = User(
                username="student",
                email="student@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.STUDENT,
                # No school_id or district_id
            )
            student.validate()  # Should not raise

    def test_cascade_behavior(self, app):
        """Test cascade behavior when deleting districts/schools."""
        with app.app_context():
            district = District(name="To Delete District")
            db.session.add(district)
            db.session.flush()

            school = School(name="To Delete School", district_id=district.id)
            db.session.add(school)
            db.session.flush()

            teacher = User(
                username="teacher",
                email="teacher@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.TEACHER,
                school_id=school.id,
                district_id=district.id,
            )
            db.session.add(teacher)
            db.session.commit()

            # Delete school - user's school_id should be set to NULL (default behavior)
            db.session.delete(school)
            db.session.commit()

            db.session.refresh(teacher)
            assert teacher.school_id is None
            # district_id should still be set
            assert teacher.district_id == district.id

            # Delete district - user's district_id should be set to NULL
            db.session.delete(district)
            db.session.commit()

            db.session.refresh(teacher)
            assert teacher.district_id is None


class TestSchoolDistrictIntegration:
    """Integration tests for School/District functionality."""

    def test_complete_hierarchy_creation(self, app):
        """Test creating complete district -> school -> user hierarchy."""
        with app.app_context():
            # Create district
            district = District(name="Integration District", code="INT001")
            db.session.add(district)
            db.session.flush()

            # Create multiple schools in district
            elementary = School(
                name="Elementary School", code="ELEM", district_id=district.id
            )
            high_school = School(
                name="High School", code="HIGH", district_id=district.id
            )
            db.session.add_all([elementary, high_school])
            db.session.flush()

            # Create users in different schools
            elem_teacher = User(
                username="elem_teacher",
                email="elem@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.TEACHER,
                school_id=elementary.id,
                district_id=district.id,
            )

            high_teacher = User(
                username="high_teacher",
                email="high@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.TEACHER,
                school_id=high_school.id,
                district_id=district.id,
            )

            observer = User(
                username="district_observer",
                email="observer@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.OBSERVER,
                school_id=elementary.id,  # Observer at elementary
                district_id=district.id,
            )

            db.session.add_all([elem_teacher, high_teacher, observer])
            db.session.commit()

            # Verify relationships
            assert district.schools.count() == 2
            assert elementary in district.schools.all()
            assert high_school in district.schools.all()

            assert district.users.count() == 3
            assert elem_teacher in district.users.all()
            assert high_teacher in district.users.all()
            assert observer in district.users.all()

            assert elementary.users.count() == 2  # elem_teacher and observer
            assert high_school.users.count() == 1  # high_teacher

            # Verify user can access district through school
            assert elem_teacher.school.district == district
            assert high_teacher.school.district == district

    def test_district_school_user_queries(self, app):
        """Test common query patterns for district/school/user relationships."""
        with app.app_context():
            # Create test data
            district1 = District(name="District 1")
            district2 = District(name="District 2")
            db.session.add_all([district1, district2])
            db.session.flush()

            school1a = School(name="School 1A", district_id=district1.id)
            school1b = School(name="School 1B", district_id=district1.id)
            school2a = School(name="School 2A", district_id=district2.id)
            db.session.add_all([school1a, school1b, school2a])
            db.session.flush()

            # Create users
            teacher1a = User(
                username="teacher1a",
                email="t1a@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.TEACHER,
                school_id=school1a.id,
                district_id=district1.id,
            )
            teacher1b = User(
                username="teacher1b",
                email="t1b@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.TEACHER,
                school_id=school1b.id,
                district_id=district1.id,
            )
            teacher2a = User(
                username="teacher2a",
                email="t2a@test.com",
                password_hash=generate_password_hash("password"),
                role=User.Role.TEACHER,
                school_id=school2a.id,
                district_id=district2.id,
            )
            db.session.add_all([teacher1a, teacher1b, teacher2a])
            db.session.commit()

            # Query all teachers in district1
            district1_teachers = User.query.filter_by(
                district_id=district1.id, role=User.Role.TEACHER
            ).all()
            assert len(district1_teachers) == 2
            assert teacher1a in district1_teachers
            assert teacher1b in district1_teachers
            assert teacher2a not in district1_teachers

            # Query all teachers in school1a
            school1a_teachers = User.query.filter_by(
                school_id=school1a.id, role=User.Role.TEACHER
            ).all()
            assert len(school1a_teachers) == 1
            assert teacher1a in school1a_teachers

            # Query all schools in district1
            district1_schools = School.query.filter_by(district_id=district1.id).all()
            assert len(district1_schools) == 2
            assert school1a in district1_schools
            assert school1b in district1_schools
            assert school2a not in district1_schools

import os
import random
import string

from werkzeug.security import generate_password_hash

from app import create_app
from models import District, Module, School, Session, Student, User, db


def _random_code(length: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def seed(num_students: int = 20) -> None:
    app = create_app(os.environ.get("FLASK_ENV"))
    with app.app_context():
        # Idempotent clear (dev only)
        db.drop_all()
        db.create_all()

        # District and School
        district = District(name="Test District", code="TD01")
        db.session.add(district)
        db.session.flush()

        school = School(name="Test High School", code="THS01", district_id=district.id)
        db.session.add(school)
        db.session.flush()

        # Default modules
        modules = [
            Module(
                name="Module 2",
                description="Data collection and analysis fundamentals",
                is_active=True,
                sort_order=1,
            ),
            Module(
                name="Module 4",
                description="Advanced data visualization and interpretation",
                is_active=True,
                sort_order=2,
            ),
            Module(
                name="Any Data Project",
                description="Open-ended data exploration project",
                is_active=True,
                sort_order=3,
            ),
        ]
        for module in modules:
            db.session.add(module)
        db.session.flush()

        # Teacher/Admin user
        teacher = User(
            username="teacher1",
            email="teacher1@example.com",
            password_hash=generate_password_hash("password123"),
            first_name="Alex",
            last_name="Teacher",
            role=User.Role.TEACHER,
            school_id=school.id,
            district_id=district.id,
            school=school.name,
            district=district.name,
        )
        db.session.add(teacher)
        db.session.flush()

        # Session (use the first module - "Module 2")
        module_2 = Module.query.filter_by(name="Module 2").first()
        session = Session(
            name="Hour 1 - Data Visualizations",
            original_name=None,
            session_code=_random_code(8),
            section=1,
            module_id=module_2.id,
            created_by_id=teacher.id,
            character_set="animals",
        )
        db.session.add(session)
        db.session.flush()

        # Students
        for i in range(1, num_students + 1):
            username = f"student{i:02d}"
            email = f"{username}@example.com"
            pin = f"{random.randint(100000, 999999)}"
            student = Student(
                username=username,
                email=email,
                password_hash=generate_password_hash(pin),
                character_name=f"Hero {i:02d}",
                teacher_id=teacher.id,
                character_description="A brave explorer",
                avatar_path=f"/avatars/hero_{i:02d}.png",
                section_id=session.id,
                device_id=None,
                pin_hash=generate_password_hash(pin),
            )
            db.session.add(student)

        db.session.commit()
        print(
            "Seed complete: "
            f"district={district.name}, school={school.name}, "
            f"teacher={teacher.username}, "
            f"session={session.session_code}, "
            f"students={num_students}"
        )


if __name__ == "__main__":
    n = int(os.environ.get("NUM_STUDENTS", "20"))
    seed(n)

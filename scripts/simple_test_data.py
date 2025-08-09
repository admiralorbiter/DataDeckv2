#!/usr/bin/env python3
"""
Simple test data population script for DataDeck v2.
Creates basic test data without complex session generation that might hang.
"""

import os
import sys

from werkzeug.security import generate_password_hash

from app import create_app
from models import District, Module, School, Session, User, db

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def create_simple_test_data():
    """Create simple test data step by step with error handling."""

    print("🏗️  Creating simple test data...")

    try:
        # Step 1: Create districts
        print("📍 Creating districts...")
        districts = []
        district_data = [
            {"name": "Metro City Schools", "code": "METRO"},
            {"name": "Riverside County", "code": "RIVER"},
        ]

        for data in district_data:
            district = District(name=data["name"], code=data["code"])
            db.session.add(district)
            districts.append(district)

        db.session.flush()
        print(f"   ✅ Created {len(districts)} districts")

        # Step 2: Create schools
        print("🏫 Creating schools...")
        schools = []
        school_data = [
            {"name": "Lincoln Elementary", "code": "LINC", "district": districts[0]},
            {"name": "Washington Middle", "code": "WASH", "district": districts[0]},
            {"name": "Oak Valley Elementary", "code": "OAKV", "district": districts[1]},
            {"name": "Pine Ridge Middle", "code": "PINE", "district": districts[1]},
        ]

        for data in school_data:
            school = School(
                name=data["name"], code=data["code"], district_id=data["district"].id
            )
            db.session.add(school)
            schools.append(school)

        db.session.flush()
        print(f"   ✅ Created {len(schools)} schools")

        # Step 3: Create admin user
        print("👤 Creating admin user...")
        admin_password_hash = generate_password_hash("nihilism")
        print(f"   🔐 Admin password hash: {admin_password_hash[:50]}...")
        admin_user = User(
            username="jonlane",
            email="jon.lane@datadeck.test",
            password_hash=admin_password_hash,
            first_name="Jon",
            last_name="Lane",
            role=User.Role.ADMIN,
            district_id=districts[0].id,
            school_id=schools[0].id,
        )
        db.session.add(admin_user)
        print("   ✅ Created admin user: jonlane / nihilism")

        # Step 4: Create teachers
        print("👨‍🏫 Creating teachers...")
        teachers = []
        teacher_data = [
            {
                "username": "alice.smith",
                "email": "alice.smith@metro.edu",
                "first_name": "Alice",
                "last_name": "Smith",
                "district": districts[0],
                "school": schools[0],
            },
            {
                "username": "bob.johnson",
                "email": "bob.johnson@metro.edu",
                "first_name": "Bob",
                "last_name": "Johnson",
                "district": districts[0],
                "school": schools[1],
            },
            {
                "username": "carol.davis",
                "email": "carol.davis@riverside.edu",
                "first_name": "Carol",
                "last_name": "Davis",
                "district": districts[1],
                "school": schools[2],
            },
            {
                "username": "david.wilson",
                "email": "david.wilson@riverside.edu",
                "first_name": "David",
                "last_name": "Wilson",
                "district": districts[1],
                "school": schools[3],
            },
        ]

        for data in teacher_data:
            teacher = User(
                username=data["username"],
                email=data["email"],
                password_hash=generate_password_hash("teacher123"),
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=User.Role.TEACHER,
                district_id=data["district"].id,
                school_id=data["school"].id,
            )
            db.session.add(teacher)
            teachers.append(teacher)

        print(f"   ✅ Created {len(teachers)} teachers")

        # Step 5: Create observers
        print("👀 Creating observers...")
        observers = []
        observer_data = [
            {
                "username": "observer.metro",
                "email": "observer@metro.edu",
                "first_name": "Metro",
                "last_name": "Observer",
                "district": districts[0],
                "school": schools[0],
            },
            {
                "username": "observer.riverside",
                "email": "observer@riverside.edu",
                "first_name": "Riverside",
                "last_name": "Observer",
                "district": districts[1],
                "school": schools[2],
            },
        ]

        for data in observer_data:
            observer = User(
                username=data["username"],
                email=data["email"],
                password_hash=generate_password_hash("observer123"),
                first_name=data["first_name"],
                last_name=data["last_name"],
                role=User.Role.OBSERVER,
                district_id=data["district"].id,
                school_id=data["school"].id,
            )
            db.session.add(observer)
            observers.append(observer)

        print(f"   ✅ Created {len(observers)} observers")

        # Step 6: Create modules
        print("📚 Creating modules...")
        modules = []
        module_data = [
            {"name": "Math Foundations", "description": "Basic math concepts"},
            {
                "name": "Science Exploration",
                "description": "Hands-on science activities",
            },
            {
                "name": "Reading Comprehension",
                "description": "Reading and analysis skills",
            },
        ]

        for data in module_data:
            module = Module(name=data["name"], description=data["description"])
            db.session.add(module)
            modules.append(module)

        db.session.flush()
        print(f"   ✅ Created {len(modules)} modules")

        # Step 7: Create more sessions for pagination testing
        print("📖 Creating sessions for pagination testing...")
        sessions = []
        import random
        from datetime import datetime, timedelta

        character_sets = ["animals", "superheroes", "fantasy", "space"]

        # Create 25 sessions across teachers to test pagination (per_page = 12)
        for i in range(25):
            teacher = teachers[i % len(teachers)]  # Rotate through teachers
            module = modules[i % len(modules)]  # Rotate through modules
            character_set = random.choice(character_sets)

            # Create unique section numbers to avoid conflicts
            section = (i % 6) + 1  # Sections 1-6

            # Create varied session names
            session_names = [
                f"{teacher.first_name}'s {module.name} - Period {section}",
                f"Advanced {module.name} Session {i+1}",
                f"{module.name} Workshop - Section {section}",
                f"Interactive {module.name} Class",
                f"{teacher.first_name}'s Special Session {i+1}",
            ]
            session_name = session_names[i % len(session_names)]

            session = Session(
                name=session_name,
                session_code=f"TEST{i+1:03d}",
                section=section,
                module_id=module.id,
                created_by_id=teacher.id,
                character_set=character_set,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            )

            # Randomly archive some sessions (20%)
            if i > 15 and random.random() < 0.2:
                session.is_archived = True
                session.archived_at = datetime.utcnow() - timedelta(
                    days=random.randint(1, 10)
                )

            # Randomly pause some active sessions (10%)
            elif i > 10 and random.random() < 0.1:
                session.is_paused = True

            db.session.add(session)
            sessions.append(session)

        print(f"   ✅ Created {len(sessions)} sessions for pagination testing")

        # Commit everything
        print("💾 Committing to database...")
        db.session.commit()

        # Verify admin login works
        print("🔍 Verifying admin login...")
        from werkzeug.security import check_password_hash

        admin_check = User.query.filter_by(username="jonlane").first()
        if admin_check and check_password_hash(admin_check.password_hash, "nihilism"):
            print("   ✅ Admin login verification: PASSED")
        else:
            print("   ❌ Admin login verification: FAILED")

        print("\n✅ Test data with pagination support created successfully!")
        print("📊 Summary:")
        print(f"   • Districts: {len(districts)}")
        print(f"   • Schools: {len(schools)}")
        print(f"   • Teachers: {len(teachers)}")
        print(f"   • Observers: {len(observers)}")
        print(f"   • Sessions: {len(sessions)} (includes active, archived, and paused)")
        print(f"   • Modules: {len(modules)}")

        # Show session breakdown
        active_count = sum(1 for s in sessions if not s.is_archived and not s.is_paused)
        archived_count = sum(1 for s in sessions if s.is_archived)
        paused_count = sum(1 for s in sessions if s.is_paused)

        print("\n📋 Session Status Breakdown:")
        print(f"   • Active: {active_count}")
        print(f"   • Archived: {archived_count}")
        print(f"   • Paused: {paused_count}")

        print("\n🧪 Test Accounts:")
        print("   Admin:     jonlane / nihilism")
        print("   Teachers:  alice.smith, bob.johnson, carol.davis, david.wilson")
        print("              Password: teacher123")
        print("   Observers: observer.metro, observer.riverside")
        print("              Password: observer123")

        print("\n🧪 Pagination Testing:")
        print("   • 25 sessions created (pagination shows at 12+ sessions)")
        print("   • Mixed status types for filter testing")
        print("   • Multiple modules and character sets")

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.session.rollback()
        raise


def main():
    """Main script entry point."""
    app = create_app()

    with app.app_context():
        print("🗄️  Setting up test database...")

        # Drop and recreate all tables
        db.drop_all()
        db.create_all()

        # Create test data
        create_simple_test_data()

        print("\n🚀 Ready to test! Run: flask run")
        print("   Navigate to: http://localhost:5000")
        print("   Login as admin: jonlane / nihilism")


if __name__ == "__main__":
    main()

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

        # Step 7: Create basic sessions (without students for now)
        print("📖 Creating basic sessions...")
        sessions = []
        session_data = [
            {
                "teacher": teachers[0],
                "name": "Alice's Math Class",
                "section": 1,
                "module": modules[0],
            },
            {
                "teacher": teachers[0],
                "name": "Alice's Science Class",
                "section": 2,
                "module": modules[1],
            },
            {
                "teacher": teachers[1],
                "name": "Bob's Reading Class",
                "section": 1,
                "module": modules[2],
            },
            {
                "teacher": teachers[2],
                "name": "Carol's Math Class",
                "section": 1,
                "module": modules[0],
            },
            {
                "teacher": teachers[3],
                "name": "David's Science Class",
                "section": 1,
                "module": modules[1],
            },
        ]

        for i, data in enumerate(session_data):
            session = Session(
                name=data["name"],
                session_code=f"TEST{i+1:03d}",  # Simple session codes
                section=data["section"],
                module_id=data["module"].id,
                created_by_id=data["teacher"].id,
                character_set="animals",
            )
            db.session.add(session)
            sessions.append(session)

        print(f"   ✅ Created {len(sessions)} basic sessions")

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

        print("\n✅ Simple test data created successfully!")
        print("📊 Summary:")
        print(f"   • Districts: {len(districts)}")
        print(f"   • Schools: {len(schools)}")
        print(f"   • Teachers: {len(teachers)}")
        print(f"   • Observers: {len(observers)}")
        print(f"   • Sessions: {len(sessions)}")
        print(f"   • Modules: {len(modules)}")

        print("\n🧪 Test Accounts:")
        print("   Admin:     jonlane / nihilism")
        print("   Teachers:  alice.smith, bob.johnson, carol.davis, david.wilson")
        print("              Password: teacher123")
        print("   Observers: observer.metro, observer.riverside")
        print("              Password: observer123")

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

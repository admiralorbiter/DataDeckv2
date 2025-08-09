#!/usr/bin/env python3
"""
Simple test data population script for DataDeck v2.
Creates basic test data without complex session generation that might hang.
"""

import os
import random
import shutil
import sys
from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from models import District, Media, Module, School, Session, Student, User, db
from models.media import MediaType

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

        # Flush to get user IDs before creating sessions
        db.session.flush()

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

            # Debug: Check if teacher has ID
            if not teacher.id:
                print(f"   Warning: Teacher {teacher.username} has no ID!")

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

        # Flush to get session IDs before creating students
        db.session.flush()

        # Step 8: Create students for testing media uploads
        print("👨‍🎓 Creating students for media testing...")
        students = create_test_students(sessions, districts, schools)
        print(f"   ✅ Created {len(students)} students")

        # Step 9: Setup uploads directory and copy test images
        print("📁 Setting up uploads directory...")
        setup_uploads_directory()
        print("   ✅ Uploads directory ready")

        # Step 10: Create media uploads for students
        print("🖼️  Creating test media uploads...")
        media_items = create_test_media(students, sessions)
        print(f"   ✅ Created {len(media_items)} media items")

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
        print(f"   • Students: {len(students)} (across first 8 active sessions)")
        print(f"   • Media Items: {len(media_items)} (individual uploads + Data Decks)")

        # Show session breakdown
        active_count = sum(1 for s in sessions if not s.is_archived and not s.is_paused)
        archived_count = sum(1 for s in sessions if s.is_archived)
        paused_count = sum(1 for s in sessions if s.is_paused)

        print("\n📋 Session Status Breakdown:")
        print(f"   • Active: {active_count}")
        print(f"   • Archived: {archived_count}")
        print(f"   • Paused: {paused_count}")

        # Show media breakdown
        individual_count = sum(1 for m in media_items if not m.is_project)
        project_count = sum(1 for m in media_items if m.is_project)
        unique_projects = len(
            set(
                m.project_group for m in media_items if m.is_project and m.project_group
            )
        )

        print("\n🖼️  Media Upload Breakdown:")
        print(f"   • Individual Images: {individual_count}")
        print(f"   • Data Deck Images: {project_count}")
        print(f"   • Total Data Decks: {unique_projects}")

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

        print("\n🖼️  Media Testing:")
        print("   • Test images copied from static/img/ to static/uploads/")
        print("   • Students have realistic data visualization titles and descriptions")
        print("   • Mix of individual uploads and Data Deck projects")
        print("   • Random reaction counts for testing badge display")
        print("   • Sample student PINs available in student list view")

        print("\n🎯 To Test M5 Media Features:")
        print("   1. Login as teacher (alice.smith / teacher123)")
        print("   2. Go to Students → View any session")
        print("   3. See student PINs in the list")
        print("   4. Login as student using district/school/PIN")
        print("   5. Test upload features and view existing media")
        print("   6. Navigate between images in Data Decks")

    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.session.rollback()
        raise


def create_test_students(sessions, districts, schools):
    """Create test students for the first few sessions."""
    students = []

    # Character names for different themes
    character_names = {
        "animals": [
            "Leo the Lion",
            "Bella the Bear",
            "Max the Monkey",
            "Luna the Llama",
            "Oscar the Owl",
            "Ruby the Rabbit",
            "Finn the Fox",
            "Zoe the Zebra",
            "Charlie the Cat",
            "Daisy the Dog",
            "Milo the Mouse",
            "Penny the Penguin",
        ],
        "superheroes": [
            "Captain Data",
            "Wonder Graph",
            "The Visualizer",
            "Chart Master",
            "Statistics Girl",
            "Professor Plot",
            "Data Detective",
            "Graph Guardian",
            "The Analyzer",
            "Metric Marvel",
            "Trend Tracker",
            "Pattern Hero",
        ],
        "fantasy": [
            "Wizard Willow",
            "Knight Nova",
            "Dragon Sage",
            "Elf Aria",
            "Mage Magnus",
            "Princess Pixel",
            "Archer Atlas",
            "Fairy Flora",
            "Dwarf Dorian",
            "Ranger Raven",
            "Sorceress Sage",
            "Paladin Phoenix",
        ],
        "space": [
            "Captain Cosmos",
            "Star Navigator",
            "Galaxy Explorer",
            "Nebula Scout",
            "Rocket Ranger",
            "Planet Hunter",
            "Comet Chaser",
            "Lunar Explorer",
            "Solar Surveyor",
            "Asteroid Ace",
            "Orbit Officer",
            "Stellar Student",
        ],
    }

    # Take first 8 sessions for student creation
    active_sessions = [s for s in sessions if not s.is_archived and not s.is_paused][:8]

    for session in active_sessions:
        # Query session from DB to get relationships loaded
        session = Session.query.get(session.id)
        session_students = []
        character_set = session.character_set
        names = character_names.get(character_set, character_names["animals"])

        # Create 8-12 students per session
        num_students = random.randint(8, 12)

        for i in range(num_students):
            character_name = names[i % len(names)]

            # Generate 6-digit PIN
            pin = f"{random.randint(100000, 999999)}"
            pin_hash = generate_password_hash(pin)

            # Create unique username from character name + session + index
            base_username = character_name.lower().replace(" ", "_").replace("the_", "")
            username = f"{base_username}_{session.id}_{i+1}"

            # Generate unique email for student
            email = f"{username}@student.datadeck.test"

            student = Student(
                username=username,
                email=email,
                password_hash=pin_hash,  # Use PIN hash as password hash
                character_name=character_name,
                teacher_id=session.created_by_id,
                section_id=session.id,
                district_id=session.created_by.district_id,
                school_id=session.created_by.school_id,
                pin_hash=pin_hash,
                current_pin=pin,  # Store plain text PIN for teacher viewing
            )

            db.session.add(student)
            students.append(student)
            session_students.append(student)

        print(f"     • {session.name}: {len(session_students)} students")

    db.session.flush()  # Get student IDs
    return students


def setup_uploads_directory():
    """Setup uploads directory and copy test images."""
    # Create uploads directory
    uploads_dir = os.path.join("static", "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    # Copy test images to uploads directory with various names
    test_images = ["test1.PNG", "test2.png", "test3.png", "test4.png"]
    source_dir = os.path.join("static", "img")

    for i, test_image in enumerate(test_images):
        source_path = os.path.join(source_dir, test_image)
        if os.path.exists(source_path):
            # Create multiple copies with different names for variety
            for j in range(3):  # 3 copies of each test image
                dest_name = f"test_upload_{i+1}_{j+1}.png"
                dest_path = os.path.join(uploads_dir, dest_name)
                try:
                    shutil.copy2(source_path, dest_path)
                except Exception as e:
                    print(f"     Warning: Could not copy {test_image}: {e}")


def create_test_media(students, sessions):
    """Create test media uploads for students."""
    media_items = []

    # Available test images in uploads directory
    test_images = []
    uploads_dir = os.path.join("static", "uploads")
    if os.path.exists(uploads_dir):
        test_images = [
            f for f in os.listdir(uploads_dir) if f.startswith("test_upload_")
        ]

    if not test_images:
        print("     Warning: No test images found in uploads directory")
        return media_items

    # Sample titles and descriptions based on your examples
    sample_data = [
        {
            "title": "UFO Sightings Analysis",
            "description": (
                "Looking at the visual, before 1994 UFO sightings hovered between "
                "150-300 yearly. From 1994 to 1997 cited reports tripled."
            ),
            "graph_tag": "line_graph",
            "variable_tag": "UFO Reports by Year",
            "is_graph": True,
        },
        {
            "title": "Height Histogram for 8th Graders in Minnesota",
            "description": (
                "I explored student heights in the class. Most students are "
                "between 145 and 155 centimeters."
            ),
            "graph_tag": "histogram",
            "variable_tag": "Height in Centimeters",
            "is_graph": True,
        },
        {
            "title": "Memory Times for 8th Graders in Minnesota",
            "description": (
                "Memory times for 8th graders in Minnesota. Half the data was "
                "below the median of 49.70 seconds, mean was 47.32 seconds."
            ),
            "graph_tag": "box_plot",
            "variable_tag": "Memory Time Score",
            "is_graph": True,
        },
        {
            "title": "Favorite Sports in Minnesota vs. New Zealand",
            "description": (
                "This dashboard shows a comparison of the favorite sports for students "
                "in Minnesota vs. New Zealand. I was surprised that both groups were "
                "into the same sports!"
            ),
            "graph_tag": "bar_chart",
            "variable_tag": "Student Responses by Sport",
            "is_graph": True,
        },
        {
            "title": "Climate Data Analysis",
            "description": "Exploring temperature trends over the past decade",
            "graph_tag": "line_graph",
            "variable_tag": "Temperature",
            "is_graph": True,
        },
        {
            "title": "Population Demographics Study",
            "description": "Breaking down population by age groups",
            "graph_tag": "pie_chart",
            "variable_tag": "Age Groups",
            "is_graph": True,
        },
        {
            "title": "Sales Performance Dashboard",
            "description": "Quarterly sales data comparison",
            "graph_tag": "bar_chart",
            "variable_tag": "Sales Revenue",
            "is_graph": True,
        },
        {
            "title": "Survey Response Analysis",
            "description": "Student survey responses about favorite subjects",
            "graph_tag": "bar_chart",
            "variable_tag": "Subject Preferences",
            "is_graph": True,
        },
    ]

    # Create individual uploads for most students
    for student in students[: len(students) // 2]:  # First half get individual uploads
        session = next((s for s in sessions if s.id == student.section_id), None)
        if not session:
            continue

        # Each student gets 1-3 individual uploads
        num_uploads = random.randint(1, 3)

        for _ in range(num_uploads):
            data = random.choice(sample_data)
            image_file = random.choice(test_images)

            # Add some variation to titles
            title_variations = [
                data["title"],
                f"{student.character_name}'s {data['title']}",
                f"Data Analysis: {data['title']}",
                f"{data['title']} - {student.character_name}",
            ]

            media = Media(
                session_id=session.id,
                student_id=student.id,
                title=random.choice(title_variations),
                description=data["description"],
                media_type=MediaType.IMAGE,
                image_file=image_file,
                is_graph=data["is_graph"],
                graph_tag=data["graph_tag"],
                variable_tag=data["variable_tag"],
                # Add some random reaction counts
                graph_likes=random.randint(0, 15),
                eye_likes=random.randint(0, 12),
                read_likes=random.randint(0, 18),
                uploaded_at=datetime.utcnow() - timedelta(days=random.randint(0, 14)),
            )

            db.session.add(media)
            media_items.append(media)

    # Create project galleries (Data Decks) for remaining students
    remaining_students = students[len(students) // 2 :]

    for student in remaining_students:
        session = next((s for s in sessions if s.id == student.section_id), None)
        if not session:
            continue

        # 60% chance of creating a Data Deck
        if random.random() < 0.6:
            # Create a Data Deck with 2-4 images
            num_images = random.randint(2, 4)
            project_group = f"project_{student.id}_{random.randint(1000, 9999)}"

            data = random.choice(sample_data)
            base_title = f"{student.character_name}'s {data['title']}"

            for i in range(num_images):
                image_file = random.choice(test_images)

                # First image is main, others are parts
                if i == 0:
                    title = base_title
                    description = data["description"]
                else:
                    title = f"{base_title} - Image {i+1}"
                    description = ""

                media = Media(
                    session_id=session.id,
                    student_id=student.id,
                    title=title,
                    description=description,
                    media_type=MediaType.IMAGE,
                    image_file=image_file,
                    is_project=True,
                    project_group=project_group,
                    is_graph=data["is_graph"],
                    graph_tag=(
                        data["graph_tag"] if i == 0 else None
                    ),  # Only main image gets tags
                    variable_tag=data["variable_tag"] if i == 0 else None,
                    # Add some random reaction counts
                    graph_likes=random.randint(0, 8),
                    eye_likes=random.randint(0, 6),
                    read_likes=random.randint(0, 10),
                    uploaded_at=datetime.utcnow()
                    - timedelta(days=random.randint(0, 10)),
                )

                db.session.add(media)
                media_items.append(media)

    db.session.flush()
    return media_items


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

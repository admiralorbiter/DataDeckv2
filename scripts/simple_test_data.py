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
from models import (
    Comment,
    District,
    Media,
    Module,
    School,
    Session,
    Student,
    StudentMediaInteraction,
    User,
    db,
)
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

        # Step 11: Create comments and interactions for M6 testing
        print("💬 Creating test comments and interactions for M6...")
        comments, interactions = create_test_comments_and_interactions(
            students, media_items, teachers
        )
        print(
            f"   ✅ Created {len(comments)} comments and "
            f"{len(interactions)} interactions"
        )

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
        print(
            f"   • Comments: {len(comments)} "
            f"(student + teacher comments with replies)"
        )
        print(
            f"   • Student Interactions: {len(interactions)} "
            f"(reactions + comment counts)"
        )

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

        print("\n💬 M6 Comments Testing:")
        print("   • ~70% of media items have 1-4 comments each")
        print("   • Mix of student and teacher comments with realistic content")
        print("   • ~30% of comment threads include replies (nested comments)")
        print("   • StudentMediaInteraction records track comment counts")
        print("   • Comments have realistic timestamps (1 hour to 1 week old)")
        print(
            "   • Student reactions (Graph Guru, Expert Engager, "
            "Supreme Storyteller) included"
        )

        print("\n🎯 To Test M5 Media Features:")
        print("   1. Login as teacher (alice.smith / teacher123)")
        print("   2. Go to Students → View any session")
        print("   3. See student PINs in the list")
        print("   4. Login as student using district/school/PIN")
        print("   5. Test upload features and view existing media")
        print("   6. Navigate between images in Data Decks")

        print("\n🎯 To Test M6 Posts & Comments Features:")
        print("   1. Login as teacher (alice.smith / teacher123)")
        print("   2. Go to Sessions → View any active session")
        print("   3. Click the 'comments' icon on media cards to view posts")
        print("   4. See existing comments from students and teachers")
        print("   5. Add new comments as a teacher")
        print("   6. Click 'Reply' to test nested comment functionality")
        print("   7. Login as student and add comments/replies")
        print("   8. Check comment counts update in session view")
        print("   9. Test 'View as Post & Comments' button in media detail")

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


def create_test_comments_and_interactions(students, media_items, teachers):
    """Create test comments and student media interactions for M6 testing."""
    comments = []
    interactions = []

    # Sample comment texts for different types
    student_comments = [
        "This is a really cool graph! I like how you showed the data.",
        "Nice work! The colors make it easy to understand.",
        "I see a clear trend in your visualization. Great job!",
        "This reminds me of our class discussion about data patterns.",
        "Cool! I want to try making a graph like this.",
        "The title explains exactly what the data shows.",
        "I notice the highest point is in the middle. Interesting!",
        "This would be perfect for our presentation.",
        "Great use of labels on your chart.",
        "I learned something new from looking at this!",
        "The data story is very clear here.",
        "Nice choice of graph type for this data.",
    ]

    teacher_comments = [
        "Excellent work! Your analysis clearly shows understanding of "
        "the data patterns.",
        "Great job on the visualization. Consider adding a trend line next time.",
        "I love how you explained your findings in the description.",
        "This demonstrates strong data literacy skills. Well done!",
        "Your graph clearly communicates the story in the data.",
        "Nice work! What other patterns do you notice?",
        "This is a perfect example of effective data visualization.",
        "Great attention to detail in your labeling and formatting.",
        "I can see you put thought into choosing the right graph type.",
        "Excellent interpretation of the data. Keep up the great work!",
        "Your analysis goes beyond just showing data - you're telling a story.",
        "This visualization would be great to share with the class.",
    ]

    reply_comments = [
        "Thank you! I worked really hard on it.",
        "Thanks for the feedback!",
        "I'm glad you liked it!",
        "Good idea! I'll try that next time.",
        "Thank you for the suggestion!",
        "I'm happy you found it interesting!",
        "Thanks! I learned a lot making this.",
        "I appreciate the encouragement!",
    ]

    # Create comments for about 70% of media items
    media_with_comments = random.sample(media_items, int(len(media_items) * 0.7))

    for media in media_with_comments:
        # Get the session and related students/teacher for this media
        session = Session.query.get(media.session_id)
        if not session:
            continue

        session_students = [s for s in students if s.section_id == session.id]
        teacher = User.query.get(session.created_by_id)

        # Create 1-4 comments per media item
        num_comments = random.randint(1, 4)
        media_comments = []

        for i in range(num_comments):
            # 60% chance of student comment, 40% chance of teacher comment
            if random.random() < 0.6 and session_students:
                # Student comment
                commenter = random.choice(session_students)
                comment_text = random.choice(student_comments)

                comment = Comment(
                    media_id=media.id,
                    text=comment_text,
                    name=commenter.character_name,
                    is_admin=False,
                    student_id=commenter.id,
                    created_at=datetime.utcnow()
                    - timedelta(hours=random.randint(1, 168)),  # 1 hour to 1 week ago
                )

                # Update or create StudentMediaInteraction for commenting student
                interaction = StudentMediaInteraction.query.filter_by(
                    student_id=commenter.id, media_id=media.id
                ).first()

                if interaction:
                    interaction.comment_count += 1
                else:
                    interaction = StudentMediaInteraction(
                        student_id=commenter.id,
                        media_id=media.id,
                        comment_count=1,
                        liked_graph=random.choice([True, False]),
                        liked_eye=random.choice([True, False]),
                        liked_read=random.choice([True, False]),
                    )
                    db.session.add(interaction)
                    interactions.append(interaction)

            else:
                # Teacher comment
                comment_text = random.choice(teacher_comments)

                comment = Comment(
                    media_id=media.id,
                    text=comment_text,
                    name=f"{teacher.first_name} {teacher.last_name}",
                    is_admin=True,
                    created_at=datetime.utcnow()
                    - timedelta(hours=random.randint(1, 168)),  # 1 hour to 1 week ago
                )

            db.session.add(comment)
            comments.append(comment)
            media_comments.append(comment)

        # Add replies to create realistic comment threads (80% chance for media
        # with 1+ comments)
        if len(media_comments) >= 1 and random.random() < 0.8:
            # Choose 1-2 comments to get replies
            num_threads = min(random.randint(1, 2), len(media_comments))
            parent_comments = random.sample(media_comments, num_threads)

            for parent_comment in parent_comments:
                # Each thread gets 1-3 replies
                num_replies = random.randint(1, 3)

                for reply_num in range(num_replies):
                    # Reply could be from student (if parent was teacher) or
                    # teacher (if parent was student)
                    if parent_comment.is_admin and session_students:
                        # Student reply to teacher comment
                        replier = random.choice(session_students)

                        if reply_num == 0:
                            reply_text = random.choice(reply_comments)
                        else:
                            # Follow-up student comments
                            followup_comments = [
                                "I have another question about this.",
                                "That makes sense now, thank you!",
                                "Can you show us more examples like this?",
                                "I want to try this approach too.",
                                "This is really helpful!",
                                "I see the pattern now.",
                            ]
                            reply_text = random.choice(followup_comments)

                        reply = Comment(
                            media_id=media.id,
                            parent_id=parent_comment.id,
                            text=reply_text,
                            name=replier.character_name,
                            is_admin=False,
                            student_id=replier.id,
                            created_at=parent_comment.created_at
                            + timedelta(
                                hours=random.randint(
                                    1 + reply_num * 12, 24 + reply_num * 12
                                )
                            ),
                        )
                    else:
                        # Teacher reply to student comment
                        if reply_num == 0:
                            teacher_replies = [
                                "Great observation! You're really thinking like a "
                                "data scientist.",
                                "Excellent question! Let me explain that further.",
                                "I love your curiosity! Here's what I think "
                                "about that...",
                                "That's exactly the kind of critical thinking "
                                "we need.",
                                "Good point!considered looking at it this way?",
                                "You're on the right track! Keep exploring that idea.",
                            ]
                            reply_text = random.choice(teacher_replies)
                        else:
                            # Follow-up teacher comments
                            followup_teacher = [
                                "Does that help clarify things?",
                                "What other patterns do you notice?",
                                "Try applying this to your own data next time.",
                                "This is a great example for the whole class.",
                                "Keep up the excellent work!",
                                "I'm impressed by your analysis skills.",
                            ]
                            reply_text = random.choice(followup_teacher)

                        reply = Comment(
                            media_id=media.id,
                            parent_id=parent_comment.id,
                            text=reply_text,
                            name=f"{teacher.first_name} {teacher.last_name}",
                            is_admin=True,
                            created_at=parent_comment.created_at
                            + timedelta(
                                hours=random.randint(
                                    2 + reply_num * 8, 36 + reply_num * 8
                                )
                            ),
                        )

                    db.session.add(reply)
                    comments.append(reply)

    # Create additional interactions for students who haven't interacted yet
    for student in students:
        # Each student interacts with 2-5 random media items from their session
        student_session_media = [
            m for m in media_items if m.session_id == student.section_id
        ]
        if not student_session_media:
            continue

        num_interactions = min(random.randint(2, 5), len(student_session_media))
        interaction_media = random.sample(student_session_media, num_interactions)

        for media in interaction_media:
            # Skip if interaction already exists
            existing = StudentMediaInteraction.query.filter_by(
                student_id=student.id, media_id=media.id
            ).first()

            if not existing:
                interaction = StudentMediaInteraction(
                    student_id=student.id,
                    media_id=media.id,
                    comment_count=0,  # No additional comments, just reactions
                    liked_graph=random.choice([True, False]),
                    liked_eye=random.choice([True, False]),
                    liked_read=random.choice([True, False]),
                )
                db.session.add(interaction)
                interactions.append(interaction)

    db.session.flush()
    return comments, interactions


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

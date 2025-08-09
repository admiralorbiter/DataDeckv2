import random
import string
from typing import Optional, Tuple

from flask import flash

from models import Session, Student, User, db


class SessionConflictError(Exception):
    """Raised when a session conflicts with an existing active session."""

    def __init__(self, existing_session: Session):
        self.existing_session = existing_session
        super().__init__(f"Active session exists: {existing_session.name}")


class SessionService:
    @staticmethod
    def generate_session_code(length: int = 8) -> str:
        """Generate a unique session code."""
        alphabet = string.ascii_uppercase + string.digits
        while True:
            code = "".join(random.choice(alphabet) for _ in range(length))
            if not Session.query.filter_by(session_code=code).first():
                return code

    @staticmethod
    def validate_session_uniqueness(
        teacher_id: int, section: int, session_id: Optional[int] = None
    ) -> Optional[Session]:
        """Check if a session conflicts with existing active sessions.

        Returns:
            None if no conflict, or the conflicting Session if one exists.
        """
        return Session.find_active_conflict(teacher_id, section, session_id)

    @staticmethod
    def create_session(
        teacher: User,
        name: str,
        section: int,
        module_id: int,
        character_set: str = "animals",
        auto_archive_existing: bool = False,
    ) -> Tuple[Session, bool]:
        """Create a new session, optionally auto-archiving conflicting sessions.

        Args:
            teacher: The teacher creating the session
            name: Session name
            section: Section/period number
            module_id: ID of the module to assign to the session
            character_set: Character set for student generation
            auto_archive_existing: If True, archive conflicting sessions automatically

        Returns:
            Tuple of (new_session, was_archived) where was_archived indicates if we
            archived an existing session

        Raises:
            SessionConflictError: If conflict exists and auto_archive_existing is False
        """
        # Check for conflicts
        existing_session = SessionService.validate_session_uniqueness(
            teacher.id, section
        )
        was_archived = False

        if existing_session:
            if auto_archive_existing:
                existing_session.archive()
                db.session.flush()  # Ensure the archive is committed
                flash(
                    f"Archived previous session '{existing_session.name}' "
                    f"to start new one.",
                    "info",
                )
                was_archived = True
            else:
                raise SessionConflictError(existing_session)

        # Create new session
        session_code = SessionService.generate_session_code()
        new_session = Session(
            name=name,
            section=section,
            module_id=module_id,
            character_set=character_set,
            session_code=session_code,
            created_by_id=teacher.id,
        )

        db.session.add(new_session)
        db.session.flush()  # Get the ID

        return new_session, was_archived

    @staticmethod
    def generate_students_for_session(
        session: Session, count: int = 20
    ) -> list[Student]:
        """Generate students for a session with unique names and PINs."""
        from werkzeug.security import generate_password_hash

        students = []
        used_names = set()
        used_pins = set()

        # Character name generators by set
        # Define name lists for readability and line length
        animal_names = [
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
        ]
        hero_prefixes = [
            "Captain",
            "Super",
            "Ultra",
            "Mega",
            "Power",
            "Storm",
            "Fire",
            "Ice",
            "Thunder",
            "Lightning",
        ]
        hero_suffixes = ["Hero", "Guardian", "Defender", "Warrior", "Knight"]
        fantasy_names = [
            "Elf",
            "Dwarf",
            "Wizard",
            "Knight",
            "Archer",
            "Mage",
            "Warrior",
            "Ranger",
            "Paladin",
            "Druid",
        ]
        space_prefixes = [
            "Star",
            "Nova",
            "Comet",
            "Galaxy",
            "Nebula",
            "Cosmos",
            "Orbit",
            "Solar",
            "Lunar",
            "Astro",
        ]
        space_suffixes = ["Explorer", "Pilot", "Navigator", "Commander", "Scout"]

        character_generators = {
            "animals": lambda i: f"{random.choice(animal_names)}{i:02d}",
            "superheroes": lambda i: (
                f"{random.choice(hero_prefixes)}{random.choice(hero_suffixes)}{i:02d}"
            ),
            "fantasy": lambda i: f"{random.choice(fantasy_names)}{i:02d}",
            "space": lambda i: (
                f"{random.choice(space_prefixes)}{random.choice(space_suffixes)}{i:02d}"
            ),
        }

        name_generator = character_generators.get(
            session.character_set, character_generators["animals"]
        )

        for i in range(1, count + 1):
            # Generate unique character name
            attempts = 0
            while attempts < 50:  # Prevent infinite loops
                character_name = name_generator(i + attempts)
                if character_name not in used_names:
                    used_names.add(character_name)
                    break
                attempts += 1
            else:
                character_name = f"Student{i:02d}"  # Fallback

            # Generate unique PIN
            attempts = 0
            while attempts < 100:
                pin = f"{random.randint(1000, 9999)}"
                if pin not in used_pins:
                    used_pins.add(pin)
                    break
                attempts += 1
            else:
                pin = f"{1000 + i}"  # Fallback

            # Create student
            username = f"student_{session.session_code}_{i:02d}".lower()
            email = f"{username}@datadeck.local"

            student = Student(
                username=username,
                email=email,
                password_hash=generate_password_hash(pin),
                character_name=character_name,
                teacher_id=session.created_by_id,
                section_id=session.id,
                pin_hash=generate_password_hash(pin),
                avatar_path=(
                    f"/static/avatars/{session.character_set}/"
                    f"{character_name.lower()}.png"
                ),
            )

            students.append(student)

        # Add all students to session
        db.session.add_all(students)
        return students

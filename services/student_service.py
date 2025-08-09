"""Student service for M4 student management operations."""

from typing import Any, Dict, List, Optional

from werkzeug.security import generate_password_hash

from models import Session, Student, db


class StudentService:
    """Service class for student-related business logic and operations."""

    @staticmethod
    def get_students_for_teacher(
        teacher_id: int, session_id: Optional[int] = None
    ) -> List[Student]:
        """Get students for a teacher, optionally filtered by session.

        Args:
            teacher_id: ID of the teacher whose students to retrieve
            session_id: Optional session ID to filter students by specific session

        Returns:
            List of Student objects ordered by character name

        Note:
            Only returns students that belong to sessions created by the teacher.
        """
        query = Student.query.filter(Student.teacher_id == teacher_id)

        if session_id:
            query = query.filter(Student.section_id == session_id)

        return query.order_by(Student.character_name).all()

    @staticmethod
    def get_student_with_ownership_check(
        student_id: int, teacher_id: int
    ) -> Optional[Student]:
        """Get a student if the teacher owns the session it belongs to.

        Args:
            student_id: ID of the student to retrieve
            teacher_id: ID of the teacher to verify ownership

        Returns:
            Student object if found and teacher owns the session, None otherwise

        Note:
            This enforces ownership security - teachers can only access students
            from sessions they created.
        """
        return (
            Student.query.filter(Student.id == student_id)
            .filter(Student.teacher_id == teacher_id)
            .first()
        )

    @staticmethod
    def delete_student_with_ownership_check(student_id: int, teacher_id: int) -> bool:
        """Delete a student if the teacher owns the session.

        Args:
            student_id: ID of the student to delete
            teacher_id: ID of the teacher requesting deletion

        Returns:
            True if student was deleted, False if not found or no permission

        Note:
            This is a soft operation - if the student doesn't exist or teacher
            doesn't own it, it returns False without raising an error.
        """
        student = StudentService.get_student_with_ownership_check(
            student_id, teacher_id
        )

        if not student:
            return False

        db.session.delete(student)
        return True

    @staticmethod
    def reset_student_pin(student_id: int, teacher_id: int) -> Optional[str]:
        """Reset a student's PIN and return the new PIN.

        Args:
            student_id: ID of the student whose PIN to reset
            teacher_id: ID of the teacher requesting the reset

        Returns:
            New PIN as string if successful, None if student not found or no permission

        Note:
            - Generates a new 4-digit PIN
            - Updates both password_hash and pin_hash fields
            - Returns the plain PIN for display to teacher (for PIN cards)
        """
        student = StudentService.get_student_with_ownership_check(
            student_id, teacher_id
        )

        if not student:
            return None

        # Generate new 4-digit PIN
        import random

        new_pin = f"{random.randint(1000, 9999)}"

        # Update hashed fields
        pin_hash = generate_password_hash(new_pin)
        student.password_hash = pin_hash
        student.pin_hash = pin_hash

        return new_pin

    @staticmethod
    def generate_pin_cards_data(
        session_id: int, teacher_id: int
    ) -> Optional[Dict[str, Any]]:
        """Generate data structure for PDF PIN cards for a session.

        Args:
            session_id: ID of the session to generate PIN cards for
            teacher_id: ID of the teacher requesting the cards (for ownership check)

        Returns:
            Dictionary with session info and student data for PDF generation,
            None if session not found or no permission

        Structure:
            {
                'session': {
                    'name': str,
                    'section': int,
                    'session_code': str,
                    'teacher_name': str
                },
                'students': [
                    {
                        'character_name': str,
                        'pin': str,  # Note:would need PIN decryption or regeneration
                        'username': str,
                        'avatar_path': str
                    }
                ]
            }

        Note:
            Since PINs are hashed, this method would need to be called during
            student generation or PIN reset when the plain PIN is available.
            Consider storing temporary PIN data for card generation.
        """
        # Get session with ownership check
        session = (
            Session.query.filter(Session.id == session_id)
            .filter(Session.created_by_id == teacher_id)
            .first()
        )

        if not session:
            return None

        # Get students for this session
        students = (
            Student.query.filter(Student.section_id == session_id)
            .order_by(Student.character_name)
            .all()
        )

        # Note: PIN extraction is problematic since they're hashed
        # This would need to be redesigned to either:
        # 1. Store temporary unhashed PINs during generation
        # 2. Regenerate all PINs when creating cards
        # 3. Add a separate PIN cards generation during session creation

        return {
            "session": {
                "name": session.name,
                "section": session.section,
                "session_code": session.session_code,
                "teacher_name": (
                    f"{session.created_by.first_name} "
                    f"{session.created_by.last_name}"
                ).strip(),
            },
            "students": [
                {
                    "character_name": student.character_name,
                    "pin": "[HASHED - REGENERATION NEEDED]",  # TODO: Fix PIN access
                    "username": student.username,
                    "avatar_path": student.avatar_path,
                }
                for student in students
            ],
        }

    @staticmethod
    def get_session_student_summary(
        session_id: int, teacher_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get summary statistics for students in a session.

        Args:
            session_id: ID of the session to summarize
            teacher_id: ID of the teacher (for ownership check)

        Returns:
            Dictionary with student summary data, None if no permission

        Structure:
            {
                'total_students': int,
                'character_themes': Dict[str, int],  # theme -> count
                'recent_activity': List[Dict], # Recent student activities (placeholder)
                'session_info': Dict[str, Any]
            }
        """
        # Get session with ownership check
        session = (
            Session.query.filter(Session.id == session_id)
            .filter(Session.created_by_id == teacher_id)
            .first()
        )

        if not session:
            return None

        students = Student.query.filter(Student.section_id == session_id).all()

        # Analyze character themes (extract from character names)
        theme_counts = {}
        for student in students:
            # Simple theme detection based on character name patterns
            name = student.character_name.lower()
            if any(
                animal in name
                for animal in [
                    "bear",
                    "wolf",
                    "eagle",
                    "lion",
                    "tiger",
                    "shark",
                    "hawk",
                    "fox",
                    "deer",
                    "owl",
                ]
            ):
                theme = "animals"
            elif any(
                hero in name
                for hero in [
                    "captain",
                    "super",
                    "ultra",
                    "mega",
                    "power",
                    "hero",
                    "guardian",
                ]
            ):
                theme = "superheroes"
            elif any(
                fantasy in name
                for fantasy in ["elf", "dwarf", "wizard", "knight", "archer", "mage"]
            ):
                theme = "fantasy"
            elif any(
                space in name
                for space in ["star", "nova", "comet", "galaxy", "nebula", "explorer"]
            ):
                theme = "space"
            else:
                theme = "other"

            theme_counts[theme] = theme_counts.get(theme, 0) + 1

        return {
            "total_students": len(students),
            "character_themes": theme_counts,
            "recent_activity": [],  # Placeholder for future media/interaction data
            "session_info": {
                "name": session.name,
                "section": session.section,
                "session_code": session.session_code,
                "character_set": session.character_set,
                "is_archived": session.is_archived,
                "is_paused": session.is_paused,
            },
        }

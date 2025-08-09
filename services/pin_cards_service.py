"""PIN Cards generation service for M4 student management."""

import io
import random
from typing import Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from werkzeug.security import generate_password_hash

from models import Session, Student


class PinCardsService:
    """Service for generating printable PIN cards for students."""

    @staticmethod
    def generate_pin_cards_pdf(
        session_id: int, teacher_id: int
    ) -> Optional[Tuple[bytes, str]]:
        """Generate PDF with PIN cards for all students in a session.

        Args:
            session_id: ID of the session to generate cards for
            teacher_id: ID of the teacher (for ownership verification)

        Returns:
            Tuple of (PDF bytes, filename) if successful, None if access denied

        Note:
            This method regenerates PINs for all students to ensure they can be
            displayed on the cards. Teachers should distribute these immediately.
        """
        # Verify session ownership
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

        if not students:
            return None

        # Generate new PINs for all students
        student_pins = PinCardsService._regenerate_student_pins(students)

        # Generate PDF
        pdf_buffer = io.BytesIO()
        pdf_filename = (
            f"pin_cards_{session.name.replace(' ', '_')}_section_{session.section}.pdf"
        )

        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        story = []
        styles = getSampleStyleSheet()

        # Title
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontSize=18,
            spaceAfter=20,
            alignment=1,  # Center alignment
        )

        story.append(Paragraph("Student PIN Cards", title_style))
        story.append(
            Paragraph(
                f"Session: {session.name} (Section {session.section})",
                styles["Heading2"],
            )
        )
        teacher_name = (
            f"{session.created_by.first_name} " f"{session.created_by.last_name}"
        ).strip()
        story.append(
            Paragraph(
                f"Teacher: {teacher_name}",
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(f"Session Code: {session.session_code}", styles["Normal"])
        )
        story.append(Spacer(1, 20))

        # Create cards in a grid (2 columns)
        cards_per_row = 2
        card_data = []

        for i in range(0, len(students), cards_per_row):
            row_students = students[i : i + cards_per_row]
            row_data = []

            for student in row_students:
                pin = student_pins.get(student.id, "****")
                card_content = PinCardsService._create_card_content(
                    student, pin, session, styles
                )
                row_data.append(card_content)

            # Fill empty cells if needed
            while len(row_data) < cards_per_row:
                row_data.append("")

            card_data.append(row_data)

        # Create table for cards
        card_table = Table(card_data, colWidths=[3.8 * inch, 3.8 * inch])
        card_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        story.append(card_table)

        # Add cutting instructions
        story.append(Spacer(1, 30))
        story.append(Paragraph("Instructions:", styles["Heading3"]))
        story.append(
            Paragraph(
                "• Cut along the grid lines to separate individual cards",
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(
                "• Distribute cards to students for easy login access", styles["Normal"]
            )
        )
        story.append(
            Paragraph(
                "• Students use their PIN to log in at the student login page",
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(
                f"• Session Code: <b>{session.session_code}</b> (backup login method)",
                styles["Normal"],
            )
        )

        # Build PDF
        doc.build(story)
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()

        return pdf_bytes, pdf_filename

    @staticmethod
    def _regenerate_student_pins(students: List[Student]) -> Dict[int, str]:
        """Regenerate PINs for a list of students and update the database.

        Args:
            students: List of Student objects to regenerate PINs for

        Returns:
            Dictionary mapping student ID to new PIN
        """
        student_pins = {}
        used_pins = set()

        for student in students:
            # Generate unique PIN
            attempts = 0
            while attempts < 100:
                pin = f"{random.randint(1000, 9999)}"
                if pin not in used_pins:
                    used_pins.add(pin)
                    break
                attempts += 1
            else:
                pin = f"{1000 + student.id}"  # Fallback using student ID

            # Update student's PIN hash
            pin_hash = generate_password_hash(pin)
            student.password_hash = pin_hash
            student.pin_hash = pin_hash

            student_pins[student.id] = pin

        return student_pins

    @staticmethod
    def _create_card_content(
        student: Student, pin: str, session: Session, styles
    ) -> str:
        """Create HTML content for a single PIN card.

        Args:
            student: Student object
            pin: Student's PIN
            session: Session object
            styles: ReportLab styles

        Returns:
            HTML string for the card content
        """
        # Determine character theme
        theme = PinCardsService._get_character_theme(student.character_name)

        card_html = f"""
        <b>{student.character_name}</b><br/>
        <font size="8">Character Name</font><br/>
        <br/>
        <b>PIN: {pin}</b><br/>
        <font size="8">Login Code</font><br/>
        <br/>
        <font size="8">Username: {student.username}</font><br/>
        <font size="8">Theme: {theme}</font><br/>
        <font size="8">Session: {session.name}</font><br/>
        <font size="8">Section: {session.section}</font>
        """

        return card_html

    @staticmethod
    def _get_character_theme(character_name: str) -> str:
        """Determine the character theme from the character name.

        Args:
            character_name: The character's name

        Returns:
            Theme name as string
        """
        name = character_name.lower()

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
            return "Animals"
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
            return "Superheroes"
        elif any(
            fantasy in name
            for fantasy in ["elf", "dwarf", "wizard", "knight", "archer", "mage"]
        ):
            return "Fantasy"
        elif any(
            space in name
            for space in ["star", "nova", "comet", "galaxy", "nebula", "explorer"]
        ):
            return "Space"
        else:
            return "Other"

    @staticmethod
    def get_session_pin_summary(session_id: int, teacher_id: int) -> Optional[Dict]:
        """Get a summary of students and their PIN status for a session.

        Args:
            session_id: ID of the session
            teacher_id: ID of the teacher (for ownership verification)

        Returns:
            Dictionary with session and student summary, None if access denied
        """
        session = (
            Session.query.filter(Session.id == session_id)
            .filter(Session.created_by_id == teacher_id)
            .first()
        )

        if not session:
            return None

        students = (
            Student.query.filter(Student.section_id == session_id)
            .order_by(Student.character_name)
            .all()
        )

        return {
            "session": {
                "id": session.id,
                "name": session.name,
                "section": session.section,
                "session_code": session.session_code,
                "character_set": session.character_set,
            },
            "students": [
                {
                    "id": student.id,
                    "character_name": student.character_name,
                    "username": student.username,
                    "theme": PinCardsService._get_character_theme(
                        student.character_name
                    ),
                }
                for student in students
            ],
            "total_students": len(students),
        }

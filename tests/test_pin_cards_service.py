"""Tests for PIN cards service (M4 implementation)."""

from unittest.mock import MagicMock, patch

from services.pin_cards_service import PinCardsService


class TestPinCardsService:
    """Test PIN cards generation service."""

    def test_generate_pin_cards_pdf_success(self, teacher_user, session_with_students):
        """Test successful PDF generation for PIN cards."""
        result = PinCardsService.generate_pin_cards_pdf(
            session_with_students.id, teacher_user.id
        )

        assert result is not None
        pdf_bytes, filename = result
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert filename.endswith(".pdf")
        assert session_with_students.name.replace(" ", "_") in filename

    def test_generate_pin_cards_pdf_unauthorized(
        self, teacher_user, session_factory, teacher_factory
    ):
        """Test PDF generation fails for unauthorized session."""
        other_teacher = teacher_factory()
        session = session_factory(created_by_id=other_teacher.id)

        result = PinCardsService.generate_pin_cards_pdf(session.id, teacher_user.id)
        assert result is None

    def test_generate_pin_cards_pdf_no_students(self, teacher_user, session_factory):
        """Test PDF generation with session that has no students."""
        session = session_factory(created_by_id=teacher_user.id)

        result = PinCardsService.generate_pin_cards_pdf(session.id, teacher_user.id)
        assert result is None

    def test_regenerate_student_pins(self, teacher_user):
        """Test PIN regeneration for multiple students."""
        from tests.factories import create_module, create_session, create_student

        # Create a single session to avoid module conflicts
        module = create_module("Test Module for PIN regeneration")
        session = create_session(teacher_user, module=module)

        students = [
            create_student(teacher_user, session),
            create_student(teacher_user, session),
            create_student(teacher_user, session),
        ]

        # Store original PIN hashes
        original_hashes = [s.pin_hash for s in students]

        new_pins = PinCardsService._regenerate_student_pins(students)

        # Verify new PINs were generated
        assert len(new_pins) == 3
        for student_id, pin in new_pins.items():
            assert len(pin) == 4
            assert pin.isdigit()

        # Verify PIN hashes were updated
        for i, student in enumerate(students):
            assert student.pin_hash != original_hashes[i]
            assert student.password_hash == student.pin_hash

    def test_get_character_theme(self):
        """Test character theme detection."""
        test_cases = [
            ("BearWarrior01", "Animals"),
            ("CaptainSuper02", "Superheroes"),
            ("ElfWizard03", "Fantasy"),
            ("StarExplorer04", "Space"),
            ("RandomName05", "Other"),
        ]

        for character_name, expected_theme in test_cases:
            theme = PinCardsService._get_character_theme(character_name)
            assert theme == expected_theme

    def test_get_session_pin_summary(self, teacher_user, session_with_students):
        """Test session PIN summary generation."""
        summary = PinCardsService.get_session_pin_summary(
            session_with_students.id, teacher_user.id
        )

        assert summary is not None
        assert "session" in summary
        assert "students" in summary
        assert "total_students" in summary

        assert summary["session"]["id"] == session_with_students.id
        assert summary["session"]["name"] == session_with_students.name
        assert summary["total_students"] > 0

    def test_get_session_pin_summary_unauthorized(
        self, teacher_user, session_factory, teacher_factory
    ):
        """Test session PIN summary fails for unauthorized access."""
        other_teacher = teacher_factory()
        session = session_factory(created_by_id=other_teacher.id)

        summary = PinCardsService.get_session_pin_summary(session.id, teacher_user.id)
        assert summary is None

    def test_create_card_content(self, student_factory, session_factory, teacher_user):
        """Test PIN card content generation."""
        session = session_factory(created_by_id=teacher_user.id)
        student = student_factory(
            teacher_id=teacher_user.id,
            character_name="BearWarrior01",
            username="test_student",
        )

        content = PinCardsService._create_card_content(
            student, "1234", session, MagicMock()
        )

        assert "BearWarrior01" in content
        assert "1234" in content
        assert "test_student" in content
        assert session.name in content

    @patch("services.pin_cards_service.SimpleDocTemplate")
    @patch("services.pin_cards_service.Table")
    def test_pdf_generation_components(
        self, mock_table, mock_doc, teacher_user, session_with_students
    ):
        """Test that PDF generation uses correct ReportLab components."""
        mock_doc_instance = MagicMock()
        mock_doc.return_value = mock_doc_instance

        PinCardsService.generate_pin_cards_pdf(
            session_with_students.id, teacher_user.id
        )

        # Verify ReportLab components were called
        mock_doc.assert_called_once()
        mock_table.assert_called_once()
        mock_doc_instance.build.assert_called_once()

    def test_pin_uniqueness_in_regeneration(self, teacher_user):
        """Test that regenerated PINs are unique."""
        from tests.factories import create_module, create_session, create_student

        # Create a single session and module to avoid duplicates
        module = create_module("Test Module for PIN uniqueness")
        session = create_session(teacher_user, module=module)

        # Create many students with the same session to avoid module conflicts
        students = [create_student(teacher_user, session) for _ in range(20)]

        new_pins = PinCardsService._regenerate_student_pins(students)

        # Verify all PINs are unique
        pin_values = list(new_pins.values())
        assert len(pin_values) == len(set(pin_values))

    def test_pin_cards_filename_generation(self, teacher_user, session_factory):
        """Test that PIN cards filename is generated correctly."""
        session = session_factory(
            created_by_id=teacher_user.id, name="Math Class Period 3", section=3
        )
        # Add at least one student so PDF generation doesn't fail
        from tests.factories import create_student

        create_student(teacher_user, session)

        result = PinCardsService.generate_pin_cards_pdf(session.id, teacher_user.id)

        assert result is not None
        pdf_bytes, filename = result

        # Check filename format
        assert "pin_cards_Math_Class_Period_3_section_3.pdf" == filename

    def test_error_handling_in_pdf_generation(self, teacher_user):
        """Test error handling in PDF generation."""
        # Test with non-existent session
        result = PinCardsService.generate_pin_cards_pdf(99999, teacher_user.id)
        assert result is None

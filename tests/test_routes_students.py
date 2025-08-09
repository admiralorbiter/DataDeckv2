"""Tests for student management routes (M4 implementation)."""

from unittest.mock import patch

import pytest
from flask import url_for

from models import Student, db
from services.student_service import StudentService


class TestStudentRoutes:
    """Test student management routes."""

    def test_student_list_requires_login(self, client):
        """Test that student list requires authentication."""
        resp = client.get(url_for("students.student_list"))
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_student_list_requires_teacher_role(self, client, observer_user):
        """Test that student list requires teacher role."""
        with client.session_transaction() as sess:
            sess["_user_id"] = str(observer_user.id)

        resp = client.get(url_for("students.student_list"))
        assert resp.status_code == 302
        # Should redirect to main index with flash message

    def test_student_list_displays_for_teacher(
        self, client, teacher_user, session_with_students
    ):
        """Test that teacher can view their students."""
        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.get(url_for("students.student_list"))
        assert resp.status_code == 200
        assert b"My Students" in resp.data

    def test_student_list_filtered_by_session(
        self, client, teacher_user, session_with_students
    ):
        """Test student list filtering by session."""
        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.get(
            url_for("students.student_list", session_id=session_with_students.id)
        )
        assert resp.status_code == 200
        assert session_with_students.name.encode() in resp.data

    def test_student_detail_requires_login(self, client):
        """Test that student detail requires authentication."""
        resp = client.get(url_for("students.student_detail", student_id=1))
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]

    def test_student_detail_with_ownership(self, client, teacher_user, student_factory):
        """Test student detail view with proper ownership."""
        student = student_factory(teacher_id=teacher_user.id)

        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.get(url_for("students.student_detail", student_id=student.id))
        assert resp.status_code == 200
        assert student.character_name.encode() in resp.data

    def test_student_detail_blocks_unauthorized_access(
        self, client, teacher_user, student_factory, teacher_factory
    ):
        """Test that teachers can't access other teachers' students."""
        other_teacher = teacher_factory()
        student = student_factory(teacher_id=other_teacher.id)

        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.get(url_for("students.student_detail", student_id=student.id))
        assert resp.status_code == 302  # Redirect due to access denied

    def test_delete_student_success(self, client, teacher_user, student_factory):
        """Test successful student deletion."""
        student = student_factory(teacher_id=teacher_user.id)

        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.delete(url_for("students.delete_student", student_id=student.id))
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["success"] is True
        assert "deleted successfully" in data["message"]

    def test_delete_student_unauthorized(
        self, client, teacher_user, student_factory, teacher_factory
    ):
        """Test that teachers can't delete other teachers' students."""
        other_teacher = teacher_factory()
        student = student_factory(teacher_id=other_teacher.id)

        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.delete(url_for("students.delete_student", student_id=student.id))
        assert resp.status_code == 404

        data = resp.get_json()
        assert data["success"] is False

    def test_reset_student_pin_success(self, client, teacher_user, student_factory):
        """Test successful PIN reset."""
        student = student_factory(teacher_id=teacher_user.id)

        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.post(url_for("students.reset_student_pin", student_id=student.id))
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["success"] is True
        assert "new_pin" in data
        assert len(data["new_pin"]) == 4

    def test_bulk_delete_students(self, client, teacher_user, student_factory):
        """Test bulk deletion of students."""
        student1 = student_factory(teacher_id=teacher_user.id)
        student2 = student_factory(teacher_id=teacher_user.id)

        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.post(
            url_for("students.delete_multiple_students"),
            json={"student_ids": [student1.id, student2.id]},
        )
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["success"] is True
        assert data["deleted_count"] == 2

    def test_analytics_endpoint(self, client, teacher_user):
        """Test analytics endpoint returns proper data."""
        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.get(url_for("students.student_analytics"))
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["success"] is True
        assert "analytics" in data
        assert "active_students" in data["analytics"]
        assert "total_uploads" in data["analytics"]
        assert "engagement_rate" in data["analytics"]

    def test_analytics_dashboard_page(self, client, teacher_user):
        """Test analytics dashboard renders correctly."""
        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.get(url_for("students.analytics_dashboard"))
        assert resp.status_code == 200
        assert b"Student Analytics" in resp.data

    def test_detailed_analytics_endpoint(self, client, teacher_user):
        """Test detailed analytics endpoint."""
        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.get(url_for("students.detailed_analytics"))
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["success"] is True
        assert "analytics" in data
        assert "sessions" in data["analytics"]
        assert "themes" in data["analytics"]


class TestPinCardsRoutes:
    """Test PIN cards functionality."""

    @patch("services.pin_cards_service.PinCardsService.generate_pin_cards_pdf")
    def test_generate_pin_cards_success(
        self, mock_generate, client, teacher_user, session_with_students
    ):
        """Test successful PIN cards generation."""
        mock_generate.return_value = (b"PDF content", "test.pdf")

        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.get(
            url_for("students.generate_pin_cards", session_id=session_with_students.id)
        )
        assert resp.status_code == 200
        assert resp.headers["Content-Type"] == "application/pdf"

    def test_generate_pin_cards_unauthorized_session(
        self, client, teacher_user, session_factory, teacher_factory
    ):
        """Test PIN cards generation with unauthorized session access."""
        other_teacher = teacher_factory()
        session = session_factory(created_by_id=other_teacher.id)

        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.get(url_for("students.generate_pin_cards", session_id=session.id))
        assert resp.status_code == 302  # Redirect due to access denied

    def test_pin_cards_preview_page(self, client, teacher_user, session_with_students):
        """Test PIN cards preview page renders correctly."""
        with client.session_transaction() as sess:
            sess["_user_id"] = str(teacher_user.id)

        resp = client.get(
            url_for("students.preview_pin_cards", session_id=session_with_students.id)
        )
        assert resp.status_code == 200
        assert b"PIN Cards Preview" in resp.data
        assert session_with_students.name.encode() in resp.data


class TestStudentServiceIntegration:
    """Test integration with StudentService."""

    def test_get_students_for_teacher(self, teacher_user, student_factory):
        """Test getting students for a teacher."""
        student1 = student_factory(teacher_id=teacher_user.id)
        student2 = student_factory(teacher_id=teacher_user.id)

        students = StudentService.get_students_for_teacher(teacher_user.id)
        assert len(students) == 2
        assert student1 in students
        assert student2 in students

    def test_get_student_with_ownership_check(
        self, teacher_user, student_factory, teacher_factory
    ):
        """Test ownership verification for student access."""
        student = student_factory(teacher_id=teacher_user.id)
        other_teacher = teacher_factory()

        # Teacher can access their own student
        result = StudentService.get_student_with_ownership_check(
            student.id, teacher_user.id
        )
        assert result == student

        # Other teacher cannot access the student
        result = StudentService.get_student_with_ownership_check(
            student.id, other_teacher.id
        )
        assert result is None

    def test_delete_student_with_ownership(self, teacher_user, student_factory):
        """Test student deletion with ownership verification."""
        student = student_factory(teacher_id=teacher_user.id)
        student_id = student.id

        success = StudentService.delete_student_with_ownership_check(
            student_id, teacher_user.id
        )
        assert success is True

        # Verify student is deleted from database
        db.session.commit()
        deleted_student = Student.query.get(student_id)
        assert deleted_student is None

    def test_reset_student_pin(self, teacher_user, student_factory):
        """Test PIN reset functionality."""
        student = student_factory(teacher_id=teacher_user.id)
        original_pin_hash = student.pin_hash

        new_pin = StudentService.reset_student_pin(student.id, teacher_user.id)
        assert new_pin is not None
        assert len(new_pin) == 4
        assert new_pin.isdigit()

        # Commit the changes and verify PIN hash was updated
        db.session.commit()
        db.session.refresh(student)
        assert student.pin_hash != original_pin_hash

    def test_get_student_portfolio(self, teacher_user, student_factory):
        """Test student portfolio data retrieval."""
        student = student_factory(teacher_id=teacher_user.id)

        portfolio = StudentService.get_student_portfolio(student.id, teacher_user.id)
        assert portfolio is not None
        assert portfolio["student"] == student
        assert "uploaded_media" in portfolio
        assert "interactions" in portfolio
        assert "comments" in portfolio
        assert "stats" in portfolio


# Test fixtures would be defined in conftest.py or imported from factories.py
@pytest.fixture
def session_with_students(session_factory, student_factory, teacher_user):
    """Create a session with students for testing."""
    session = session_factory(created_by_id=teacher_user.id)
    # Create some students for the session
    for i in range(3):
        student_factory(teacher_id=teacher_user.id, section_id=session.id)
    return session

import io
import os
import pytest
from flask import url_for
from werkzeug.security import generate_password_hash
from werkzeug.datastructures import FileStorage
from PIL import Image

from models import District, Module, School, Session, User, Student, Media, db


@pytest.fixture
def test_data_setup(app):
    """Set up district, school, module, teachers, sessions, and student."""
    with app.app_context():
        district = District(name="Test District", code="TDIST")
        db.session.add(district)
        db.session.flush()

        school = School(name="Test School", code="TSCHL", district_id=district.id)
        db.session.add(school)
        db.session.flush()

        module = Module(name="Test Module", description="Test Desc", is_active=True, sort_order=1)
        db.session.add(module)
        db.session.flush()

        teacher = User(
            username="teacher1",
            email="teacher1@test.com",
            password_hash=generate_password_hash("password"),
            role=User.Role.TEACHER,
            school_id=school.id,
            district_id=district.id,
        )
        db.session.add(teacher)

        other_teacher = User(
            username="teacher2",
            email="teacher2@test.com",
            password_hash=generate_password_hash("password"),
            role=User.Role.TEACHER,
            school_id=school.id,
            district_id=district.id,
        )
        db.session.add(other_teacher)
        db.session.flush()

        sess = Session(
            name="Teacher 1 Session",
            section=1,
            module_id=module.id,
            session_code="SESS123",
            created_by_id=teacher.id,
            character_set="animals",
        )
        db.session.add(sess)
        db.session.flush()

        student = Student(
            username="student1",
            email="student1@test.com",
            password_hash=generate_password_hash("123456"),
            character_name="Hero-Fox",
            teacher_id=teacher.id,
            section_id=sess.id,
            pin_hash=generate_password_hash("123456"),
            current_pin="123456"
        )
        db.session.add(student)
        db.session.commit()

        yield {
            "teacher_id": teacher.id,
            "teacher_email": teacher.email,
            "other_teacher_id": other_teacher.id,
            "other_teacher_email": other_teacher.email,
            "session_id": sess.id,
            "student_id": student.id,
            "student_username": student.username,
        }


def generate_mock_image_file(filename="test.png"):
    """Generate a mock image in memory using PIL."""
    file = io.BytesIO()
    image = Image.new("RGB", size=(100, 100), color=(255, 0, 0))
    image.save(file, "PNG")
    file.seek(0)
    return FileStorage(stream=file, filename=filename, content_type="image/png")


class TestMediaUploadRoutes:
    """Test unified media upload flows for both students and teachers."""

    def test_student_upload_single_success(self, client, test_data_setup):
        """Test student uploading exactly 1 image; should auto-detect and save as single media."""
        # Log in student
        with client.session_transaction() as sess:
            sess["student_id"] = test_data_setup["student_id"]

        mock_image = generate_mock_image_file("my_viz.png")

        # POST upload single image via unified route
        response = client.post(
            "/media/upload",
            data={
                "files": [mock_image],
                "title": "My Awesome Data Viz",
                "description": "Showing variable patterns",
                "is_graph": "y",
                "graph_tag": "bar_chart",
                "variable_tag": "Sales",
            },
            follow_redirects=True
        )

        assert response.status_code == 200
        
        # Verify DB entry
        media = Media.query.filter_by(student_id=test_data_setup["student_id"]).first()
        assert media is not None
        assert media.title == "My Awesome Data Viz"
        assert media.description == "Showing variable patterns"
        assert media.is_graph is True
        assert media.graph_tag == "bar_chart"
        assert media.variable_tag == "Sales"
        assert media.posted_by_admin_id is None
        assert media.is_project is False  # Auto-detected single

        # Verify EXIF is cleared (we verify local processed file exists and metadata is clear)
        uploads_dir = os.path.join(client.application.root_path, "static", "uploads")
        file_path = os.path.join(uploads_dir, media.image_file)
        assert os.path.exists(file_path)
        
        with Image.open(file_path) as img:
            assert "exif" not in img.info
            
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
        thumb_path = file_path.replace(".", "_thumb.")
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

    def test_student_upload_project_success(self, client, test_data_setup):
        """Test student uploading multiple images (2-5); should save as project gallery."""
        # Log in student
        with client.session_transaction() as sess:
            sess["student_id"] = test_data_setup["student_id"]

        mock_image1 = generate_mock_image_file("step1.png")
        mock_image2 = generate_mock_image_file("step2.png")
        mock_image3 = generate_mock_image_file("step3.png")

        # POST upload project via unified route
        response = client.post(
            "/media/upload",
            data={
                "files": [mock_image1, mock_image2, mock_image3],
                "title": "Student Multi-step Project",
                "description": "Progressive charts",
                "is_graph": "y",
                "graph_tag": "line_graph",
                "variable_tag": "Temperature",
            },
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify DB entries
        project_media = Media.query.filter_by(
            student_id=test_data_setup["student_id"],
            is_project=True
        ).all()
        
        assert len(project_media) == 3
        assert project_media[0].project_group == project_media[1].project_group
        assert project_media[0].title == "Student Multi-step Project"
        assert project_media[1].title == "Student Multi-step Project - Image 2"
        assert project_media[2].title == "Student Multi-step Project - Image 3"
        assert project_media[0].is_project is True

        # Cleanup files
        for media in project_media:
            uploads_dir = os.path.join(client.application.root_path, "static", "uploads")
            file_path = os.path.join(uploads_dir, media.image_file)
            if os.path.exists(file_path):
                os.remove(file_path)
            thumb_path = file_path.replace(".", "_thumb.")
            if os.path.exists(thumb_path):
                os.remove(thumb_path)

    def test_student_upload_too_many_files(self, client, test_data_setup):
        """Test that uploading more than 5 files fails validation."""
        with client.session_transaction() as sess:
            sess["student_id"] = test_data_setup["student_id"]

        files = [generate_mock_image_file(f"image_{i}.png") for i in range(6)]

        # POST upload project with 6 files
        response = client.post(
            "/media/upload",
            data={
                "files": files,
                "title": "Too Many Files Project",
            },
            follow_redirects=True
        )

        # Verification that no Media was created
        media_count = Media.query.filter_by(student_id=test_data_setup["student_id"]).count()
        assert media_count == 0

    def test_teacher_upload_single_success(self, client, test_data_setup):
        """Test teacher uploading 1 example image; saved as single upload."""
        # Log in teacher
        client.post(
            "/login",
            data={
                "username": test_data_setup["teacher_email"],
                "password": "password",
                "csrf_token": "test",
            }
        )

        mock_image = generate_mock_image_file("teacher_example.png")

        # POST single upload to teacher route
        response = client.post(
            f"/sessions/{test_data_setup['session_id']}/media/upload",
            data={
                "files": [mock_image],
                "title": "Teacher Lesson Example",
                "description": "Important reference chart",
                "is_graph": "y",
                "graph_tag": "scatter_plot",
                "variable_tag": "Population Density",
            },
            follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Teacher Lesson Example" in response.data

        # Verify DB entry
        media = Media.query.filter_by(session_id=test_data_setup["session_id"], student_id=None).first()
        assert media is not None
        assert media.posted_by_admin_id == test_data_setup["teacher_id"]
        assert media.title == "Teacher Lesson Example"
        assert media.is_project is False  # Auto-detected single

        # Cleanup
        uploads_dir = os.path.join(client.application.root_path, "static", "uploads")
        file_path = os.path.join(uploads_dir, media.image_file)
        if os.path.exists(file_path):
            os.remove(file_path)
        thumb_path = file_path.replace(".", "_thumb.")
        if os.path.exists(thumb_path):
            os.remove(thumb_path)

    def test_teacher_upload_project_success(self, client, test_data_setup):
        """Test teacher uploading multiple slides (2-5); saved as project."""
        # Log in teacher
        client.post(
            "/login",
            data={
                "username": test_data_setup["teacher_email"],
                "password": "password",
                "csrf_token": "test",
            }
        )

        mock_image1 = generate_mock_image_file("teacher_slide1.png")
        mock_image2 = generate_mock_image_file("teacher_slide2.png")

        # POST project upload to teacher route
        response = client.post(
            f"/sessions/{test_data_setup['session_id']}/media/upload",
            data={
                "files": [mock_image1, mock_image2],
                "title": "Teacher Multi-chart Deck",
                "description": "Comparative classroom examples",
                "is_graph": "y",
                "graph_tag": "mixed",
                "variable_tag": "GDP vs Life Expectancy",
            },
            follow_redirects=True
        )

        assert response.status_code == 200

        # Verify DB entry
        media_items = Media.query.filter_by(
            session_id=test_data_setup["session_id"],
            student_id=None,
            is_project=True
        ).all()

        assert len(media_items) == 2
        assert media_items[0].posted_by_admin_id == test_data_setup["teacher_id"]
        assert media_items[0].title == "Teacher Multi-chart Deck"
        assert media_items[1].title == "Teacher Multi-chart Deck - Image 2"

        # Cleanup
        for media in media_items:
            uploads_dir = os.path.join(client.application.root_path, "static", "uploads")
            file_path = os.path.join(uploads_dir, media.image_file)
            if os.path.exists(file_path):
                os.remove(file_path)
            thumb_path = file_path.replace(".", "_thumb.")
            if os.path.exists(thumb_path):
                os.remove(thumb_path)

    def test_teacher_upload_unauthorized_session(self, client, test_data_setup):
        """Test teacher is blocked from uploading to a session owned by another teacher."""
        # Log in other teacher
        client.post(
            "/login",
            data={
                "username": test_data_setup["other_teacher_email"],
                "password": "password",
                "csrf_token": "test",
            }
        )

        mock_image = generate_mock_image_file("illegal_upload.png")

        # Try to POST to the first teacher's session
        response = client.post(
            f"/sessions/{test_data_setup['session_id']}/media/upload",
            data={
                "files": [mock_image],
                "title": "Spying on other session",
            },
            follow_redirects=True
        )

        # Should redirect
        assert response.status_code == 200
        # Verification that no Media was created for this session by other teacher
        media = Media.query.filter_by(
            session_id=test_data_setup["session_id"],
            posted_by_admin_id=test_data_setup["other_teacher_id"]
        ).first()
        assert media is None

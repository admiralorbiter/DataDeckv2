import pytest

from models import Comment, Media, Session, Student, StudentMediaInteraction, User, db


@pytest.fixture
def teacher(app):
    with app.app_context():
        teacher = User(
            username="teachermodel",
            email="teachermodel@example.com",
            password_hash="hash",
            role=User.Role.TEACHER,
            school="School A",
            district="District A",
        )
        db.session.add(teacher)
        db.session.commit()
        yield teacher


def test_session_media_indexes_exist(app, teacher):
    with app.app_context():
        session = Session(
            name="Hour 1",
            session_code="ABCDEFGH",
            section=1,
            module="2",
            created_by_id=teacher.id,
        )
        db.session.add(session)
        db.session.commit()

        media = Media(
            session_id=session.id,
            title="Image 1",
            media_type="image",
            image_file="/tmp/1.png",
            graph_tag="trend",
            variable_tag="y",
        )
        db.session.add(media)
        db.session.commit()

        assert media.id is not None
        assert media.session_id == session.id


def test_student_and_interaction_unique_constraint(app, teacher):
    with app.app_context():
        session = Session(
            name="Hour 2",
            session_code="HGFEDCBA",
            section=2,
            module="2",
            created_by_id=teacher.id,
        )
        db.session.add(session)
        db.session.commit()

        student = Student(
            username="stud1",
            email="stud1@example.com",
            password_hash="hash",
            character_name="Hero",
            teacher_id=teacher.id,
            section_id=session.id,
        )
        db.session.add(student)
        db.session.commit()

        media = Media(
            session_id=session.id,
            title="Image 2",
            media_type="image",
            image_file="/tmp/2.png",
        )
        db.session.add(media)
        db.session.commit()

        inter1 = StudentMediaInteraction(
            student_id=student.id, media_id=media.id, liked_graph=True
        )
        db.session.add(inter1)
        db.session.commit()

        with pytest.raises(Exception):
            inter2 = StudentMediaInteraction(
                student_id=student.id, media_id=media.id, liked_eye=True
            )
            db.session.add(inter2)
            db.session.commit()


def test_comment_self_relationship(app, teacher):
    with app.app_context():
        session = Session(
            name="Hour 3",
            session_code="ZXCVBNMA",
            section=3,
            module="2",
            created_by_id=teacher.id,
        )
        db.session.add(session)
        db.session.commit()

        media = Media(
            session_id=session.id,
            title="Image 3",
            media_type="image",
            image_file="/tmp/3.png",
        )
        db.session.add(media)
        db.session.commit()

        parent = Comment(media_id=media.id, text="Parent", is_admin=True)
        db.session.add(parent)
        db.session.commit()

        child = Comment(
            media_id=media.id, parent_id=parent.id, text="Child", is_admin=False
        )
        db.session.add(child)
        db.session.commit()

        assert child.parent_id == parent.id
        assert parent.replies.count() == 1

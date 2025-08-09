from models import db
from tests.factories import (
    create_comment,
    create_district,
    create_interaction,
    create_media,
    create_school,
    create_session,
    create_student,
    create_teacher,
)


def test_factories_flow(app):
    with app.app_context():
        district = create_district()
        school = create_school(district)
        teacher = create_teacher(district, school)
        session = create_session(teacher, section=1)
        student = create_student(teacher, session)
        media = create_media(session, posted_by=teacher)
        parent = create_comment(media, as_admin=True)
        child = create_comment(media, parent=parent, as_admin=False)
        inter = create_interaction(student, media, graph=True)

        db.session.commit()

        assert teacher.id
        assert session.id
        assert student.section_id == session.id
        assert media.session_id == session.id
        assert child.parent_id == parent.id
        assert inter.student_id == student.id
        assert inter.media_id == media.id

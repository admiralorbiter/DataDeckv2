import random
import string

from werkzeug.security import generate_password_hash

from models import (
    Comment,
    District,
    Media,
    Session,
    Student,
    StudentMediaInteraction,
    User,
    db,
)


def rand_code(n: int = 8) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(n))


def create_district(name: str | None = None, code: str | None = None) -> District:
    d = District(name=name or f"District-{rand_code(4)}", code=code or rand_code(5))
    db.session.add(d)
    db.session.flush()
    return d


def create_school(district: District, name: str | None = None, code: str | None = None):
    from models import School

    s = School(
        name=name or f"School-{rand_code(4)}",
        code=code or rand_code(5),
        district_id=district.id,
    )
    db.session.add(s)
    db.session.flush()
    return s


def create_teacher(district: District, school, username: str | None = None) -> User:
    teacher = User(
        username=username or f"teacher_{rand_code(4)}",
        email=f"{rand_code(6).lower()}@example.com",
        password_hash=generate_password_hash("password123"),
        role=User.Role.TEACHER,
        school_id=school.id,
        district_id=district.id,
        school=school.name,
        district=district.name,
    )
    db.session.add(teacher)
    db.session.flush()
    return teacher


def create_session(teacher: User, section: int = 1) -> Session:
    sess = Session(
        name=f"Hour {section}",
        session_code=rand_code(8),
        section=section,
        module="2",
        created_by_id=teacher.id,
        character_set="animals",
    )
    db.session.add(sess)
    db.session.flush()
    return sess


def create_student(teacher: User, session: Session) -> Student:
    pin = str(random.randint(1000, 9999))
    student = Student(
        username=f"student_{rand_code(5).lower()}",
        email=f"{rand_code(6).lower()}@example.com",
        password_hash=generate_password_hash(pin),
        character_name=f"Hero-{rand_code(3)}",
        teacher_id=teacher.id,
        section_id=session.id,
        pin_hash=generate_password_hash(pin),
    )
    db.session.add(student)
    db.session.flush()
    return student


def create_media(session: Session, posted_by: User | None = None) -> Media:
    m = Media(
        session_id=session.id,
        title=f"Media-{rand_code(4)}",
        media_type="image",
        image_file=f"/tmp/{rand_code(6)}.png",
        posted_by_admin_id=posted_by.id if posted_by else None,
    )
    db.session.add(m)
    db.session.flush()
    return m


def create_comment(
    media: Media, parent: Comment | None = None, as_admin: bool = True
) -> Comment:
    c = Comment(
        media_id=media.id,
        parent_id=parent.id if parent else None,
        text=f"Comment {rand_code(5)}",
        is_admin=as_admin,
    )
    db.session.add(c)
    db.session.flush()
    return c


def create_interaction(
    student: Student, media: Media, graph: bool = True
) -> StudentMediaInteraction:
    inter = StudentMediaInteraction(
        student_id=student.id,
        media_id=media.id,
        liked_graph=graph,
        liked_eye=not graph,
    )
    db.session.add(inter)
    db.session.flush()
    return inter

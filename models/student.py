from .base import db
from .user import User


class Student(User):
    __tablename__ = "students"

    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)
    character_name = db.Column(db.String(64), nullable=False)
    character_description = db.Column(db.Text)
    avatar_path = db.Column(db.String(256))
    teacher_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey("sessions.id"))
    device_id = db.Column(db.String(128))
    pin_hash = db.Column(db.String(128))

    # Use polymorphic identity to distinguish Student from User
    __mapper_args__ = {
        "polymorphic_identity": "student",
        # Disambiguate joined-table inheritance when multiple FKs target users.id
        "inherit_condition": id == User.id,
    }

    # Relationship to teacher
    teacher = db.relationship(
        "User",
        foreign_keys=[teacher_id],
        backref=db.backref("students", lazy="dynamic"),
    )

    # Relationship to session/section
    section = db.relationship(
        "Session",
        foreign_keys=[section_id],
        backref=db.backref("students", lazy="dynamic", cascade="all, delete-orphan"),
    )

    def __init__(
        self, username, email, password_hash, character_name, teacher_id, **kwargs
    ):
        super().__init__(
            username=username,
            email=email,
            password_hash=password_hash,
            role=User.Role.STUDENT,
            **kwargs,
        )
        self.character_name = character_name
        self.teacher_id = teacher_id

    def __repr__(self):
        return f"<Student {self.character_name} (ID: {self.id})>"

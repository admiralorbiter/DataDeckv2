from .base import BaseModel, db


class StudentMediaInteraction(BaseModel):
    __tablename__ = "student_media_interactions"

    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey("media.id"), nullable=False)
    liked_graph = db.Column(db.Boolean, nullable=False, default=False)
    liked_eye = db.Column(db.Boolean, nullable=False, default=False)
    liked_read = db.Column(db.Boolean, nullable=False, default=False)
    comment_count = db.Column(db.Integer, nullable=False, default=0)

    # Relationships
    student = db.relationship(
        "Student",
        foreign_keys=[student_id],
        backref=db.backref("interactions", lazy="dynamic"),
    )
    media = db.relationship(
        "Media",
        foreign_keys=[media_id],
        backref=db.backref("interactions", lazy="dynamic"),
    )

    __table_args__ = (
        db.UniqueConstraint("student_id", "media_id", name="uq_student_media"),
    )

from uuid import uuid4

from .base import BaseModel, db


class MediaType:
    IMAGE = "image"
    VIDEO = "video"


class Media(BaseModel):
    __tablename__ = "media"

    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    media_type = db.Column(
        db.Enum(MediaType.IMAGE, MediaType.VIDEO, name="media_type_enum"),
        nullable=False,
    )
    video_file = db.Column(db.String(512))
    image_file = db.Column(db.String(512))
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # Reaction counts (cached/derived)
    graph_likes = db.Column(db.Integer, nullable=False, default=0)
    eye_likes = db.Column(db.Integer, nullable=False, default=0)
    read_likes = db.Column(db.Integer, nullable=False, default=0)

    # Tagging/flags
    graph_tag = db.Column(db.String(64))
    is_graph = db.Column(db.Boolean, nullable=False, default=False)
    variable_tag = db.Column(db.String(64))
    submitted_password = db.Column(db.String(128))

    # Poster relationships
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    posted_by_admin_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    # Project support
    project_group = db.Column(db.String(36))  # uuid string
    project_images = db.Column(db.JSON)
    is_project = db.Column(db.Boolean, nullable=False, default=False)

    # Relationships
    session = db.relationship(
        "Session",
        foreign_keys=[session_id],
        backref=db.backref(
            "media",
            lazy="dynamic",
            order_by="desc(Media.uploaded_at)",
            cascade="all, delete-orphan",
        ),
    )
    student = db.relationship(
        "Student",
        foreign_keys=[student_id],
        backref=db.backref("media", lazy="dynamic"),
    )
    posted_by_admin = db.relationship("User", foreign_keys=[posted_by_admin_id])

    def ensure_project_group(self):
        if self.is_project and not self.project_group:
            self.project_group = str(uuid4())

    __table_args__ = (
        db.Index("ix_media_session_uploaded", "session_id", "uploaded_at"),
        db.Index("ix_media_media_type", "media_type"),
        db.Index("ix_media_graph_tag", "graph_tag"),
        db.Index("ix_media_variable_tag", "variable_tag"),
    )

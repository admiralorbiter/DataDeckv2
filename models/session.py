from datetime import datetime, timezone
from enum import Enum

from .base import BaseModel, db


class Module(Enum):
    MODULE_2 = "2"
    MODULE_4 = "4"

    @property
    def display_name(self):
        return f"Module {self.value}"


class Session(BaseModel):
    __tablename__ = "sessions"

    name = db.Column(db.String(128), nullable=False)
    original_name = db.Column(db.String(128))
    session_code = db.Column(db.String(8), unique=True, nullable=False)
    section = db.Column(db.Integer, nullable=False)
    module = db.Column(db.Enum(Module), nullable=False)
    is_paused = db.Column(db.Boolean, nullable=False, default=False)
    is_archived = db.Column(db.Boolean, nullable=False, default=False)
    archived_at = db.Column(db.DateTime)
    character_set = db.Column(db.String(64))

    # Foreign keys
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Relationships
    created_by = db.relationship("User", foreign_keys=[created_by_id])

    # Helper methods
    def archive(self):
        if not self.is_archived:
            self.is_archived = True
            self.archived_at = datetime.now(timezone.utc)

    @classmethod
    def find_active_conflict(cls, teacher_id, section, exclude_session_id=None):
        """Find existing active session that conflicts with given teacher/section."""
        query = cls.query.filter(
            cls.created_by_id == teacher_id,
            cls.section == section,
            cls.is_archived is False,
        )
        if exclude_session_id:
            query = query.filter(cls.id != exclude_session_id)
        return query.first()

    def __repr__(self):
        return (
            f"<Session {self.name} "
            f"(Section {self.section}, {self.module.display_name})>"
        )

    __table_args__ = (
        db.Index(
            "ix_sessions_created_by_section_archived",
            "created_by_id",
            "section",
            "is_archived",
        ),
    )

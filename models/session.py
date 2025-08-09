from datetime import datetime

from .base import BaseModel, db


class Session(BaseModel):
    __tablename__ = "sessions"

    name = db.Column(db.String(128), nullable=False)
    original_name = db.Column(db.String(128))
    session_code = db.Column(db.String(8), unique=True, nullable=False)
    section = db.Column(db.Integer, nullable=False)
    module = db.Column(db.Enum("2", "4", name="module_enum"), nullable=False)
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
            self.archived_at = datetime.utcnow()

    __table_args__ = (
        db.Index(
            "ix_sessions_created_by_section_archived",
            "created_by_id",
            "section",
            "is_archived",
        ),
    )

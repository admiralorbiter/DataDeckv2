from .base import BaseModel, db


class Module(BaseModel):
    """Curriculum module that can be assigned to sessions.

    Admin-configurable modules allow flexibility in curriculum design.
    Teachers can select from active modules when creating sessions.
    """

    __tablename__ = "modules"

    name = db.Column(db.String(128), nullable=False, unique=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    sort_order = db.Column(db.Integer, default=0)  # For admin ordering

    # Relationships
    sessions = db.relationship("Session", back_populates="module")

    def __repr__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"<Module {self.name} ({status})>"

    @classmethod
    def get_active_modules(cls):
        """Get all active modules ordered by sort_order, then name."""
        return (
            cls.query.filter(cls.is_active == True)  # noqa: E712
            .order_by(cls.sort_order.asc(), cls.name.asc())
            .all()
        )

    @classmethod
    def get_choices_for_form(cls):
        """Get (id, name) tuples for form SelectField choices."""
        modules = cls.get_active_modules()
        return [(module.id, module.name) for module in modules]

    def activate(self):
        """Mark module as active."""
        self.is_active = True

    def deactivate(self):
        """Mark module as inactive."""
        self.is_active = False

    __table_args__ = (db.Index("ix_modules_active_sort", "is_active", "sort_order"),)

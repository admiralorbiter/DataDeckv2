from .base import db
from .user import User


class Observer(User):
    __tablename__ = "observers"

    id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)

    # Observer-specific fields
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "observer",
        # Disambiguate joined-table inheritance when multiple FKs target users.id
        "inherit_condition": id == User.id,
    }

    # Creator relationship (typically an admin/teacher who invited the observer)
    created_by = db.relationship("User", foreign_keys=[created_by_id])

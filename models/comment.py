from .base import BaseModel, db


class Comment(BaseModel):
    __tablename__ = "comments"

    media_id = db.Column(db.Integer, db.ForeignKey("media.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id"))
    text = db.Column(db.Text, nullable=False)
    name = db.Column(db.String(128))
    device_id = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"))
    admin_avatar = db.Column(db.String(256))

    # Relationships
    media = db.relationship(
        "Media", foreign_keys=[media_id], backref=db.backref("comments", lazy="dynamic")
    )
    # Use a lambda to avoid Python built-in `id` and ensure proper late-binding
    parent = db.relationship(
        "Comment",
        remote_side=lambda: [Comment.id],
        backref=db.backref("replies", lazy="dynamic"),
    )

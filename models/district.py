from .base import BaseModel, db


class District(BaseModel):
    __tablename__ = "districts"

    name = db.Column(db.String(128), unique=True, nullable=False)
    code = db.Column(db.String(32), unique=True)

    # Relationships
    schools = db.relationship("School", back_populates="district", lazy="dynamic")
    users = db.relationship("User", back_populates="district", lazy="dynamic")

    def __repr__(self):
        return f"<District {self.name}>"

from .base import BaseModel, db


class School(BaseModel):
    __tablename__ = "schools"

    name = db.Column(db.String(128), nullable=False)
    code = db.Column(db.String(32), unique=True)
    district_id = db.Column(db.Integer, db.ForeignKey("districts.id"), nullable=False)

    # Relationships
    district = db.relationship("District", back_populates="schools")
    users = db.relationship("User", back_populates="school_rel", lazy="dynamic")

    def __repr__(self):
        return f"<School {self.name}>"

from enum import Enum
from flask_login import UserMixin
from .base import db, BaseModel
from datetime import datetime, timezone

class User(BaseModel, UserMixin):
    __tablename__ = 'users'
    
    # Add type discriminator column
    type = db.Column(db.String(50))
    
    # Add polymorphic identity
    __mapper_args__ = {
        'polymorphic_identity': 'user',
        'polymorphic_on': type
    }
    
    class Role(Enum):
        STUDENT = 'student'
        TEACHER = 'teacher'
        OBSERVER = 'observer'
        STAFF = 'staff'
        ADMIN = 'admin'
    
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    role = db.Column(db.Enum(Role), nullable=False, default=Role.STUDENT)
    
    # Foreign keys for school and district
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=True)
    district_id = db.Column(db.Integer, db.ForeignKey('districts.id'), nullable=True)
    
    # Relationships
    school = db.relationship('School', back_populates='users')
    district = db.relationship('District', back_populates='users')

    # Helper methods for role checking
    def is_admin(self):
        return self.role == self.Role.ADMIN

    def is_staff(self):
        return self.role == self.Role.STAFF

    def is_teacher(self):
        return self.role == self.Role.TEACHER

    def is_observer(self):
        return self.role == self.Role.OBSERVER

    def is_student(self):
        return self.role == self.Role.STUDENT

    def requires_school_info(self):
        """Check if the user role requires school and district information"""
        return self.role in [self.Role.TEACHER, self.Role.OBSERVER]

    def validate(self):
        """Validate user data based on role"""
        if self.requires_school_info():
            if not self.school_id or not self.district_id:
                return False, "Teachers and Observers must have both school and district assigned"
        return True, "Validation successful" 
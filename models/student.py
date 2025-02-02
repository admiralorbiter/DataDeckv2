from .user import User
from .base import db

class Student(User):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    character_name = db.Column(db.String(64), nullable=False)
    character_description = db.Column(db.Text)
    avatar_path = db.Column(db.String(256))
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Use polymorphic identity to distinguish Student from User
    __mapper_args__ = {
        'polymorphic_identity': 'student',
    }
    
    # Relationship to teacher
    teacher = db.relationship(
        'User',
        foreign_keys=[teacher_id],
        backref=db.backref('students', lazy='dynamic')
    )
    
    def __init__(self, username, email, password_hash, character_name, teacher_id, **kwargs):
        super().__init__(
            username=username,
            email=email,
            password_hash=password_hash,
            role=User.Role.STUDENT,
            **kwargs
        )
        self.character_name = character_name
        self.teacher_id = teacher_id 
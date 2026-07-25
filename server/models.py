from datetime import date

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates

from config import db, bcrypt


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String, nullable=False)

    # A User has many Workouts; deleting a user cleans up their workouts too.
    workouts = db.relationship('Workout', back_populates='user', cascade='all, delete-orphan')

    # ---- Secure password handling ----
    # The raw password is never stored or readable. Accessing `password_hash`
    # raises an error; only *setting* it (which hashes it) is allowed.
    @hybrid_property
    def password_hash(self):
        raise AttributeError('Password hashes may not be viewed.')

    @password_hash.setter
    def password_hash(self, password):
        hashed = bcrypt.generate_password_hash(password.encode('utf-8'))
        self._password_hash = hashed.decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))

    # ---- Model validations ----
    @validates('username')
    def validate_username(self, key, value):
        if not value or not value.strip():
            raise ValueError('Username cannot be empty.')
        return value.strip()

    def __repr__(self):
        return f'<User {self.id}: {self.username}>'


class Workout(db.Model):
    __tablename__ = 'workouts'
    __table_args__ = (
        db.CheckConstraint('duration_minutes > 0', name='ck_workout_duration_positive'),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    duration_minutes = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)

    # Every workout belongs to exactly one user (ownership for access control).
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', back_populates='workouts')

    # ---- Model validations ----
    @validates('title')
    def validate_title(self, key, value):
        if not value or not value.strip():
            raise ValueError('Title cannot be empty.')
        return value.strip()

    @validates('duration_minutes')
    def validate_duration(self, key, value):
        if value is None or value <= 0:
            raise ValueError('duration_minutes must be a positive integer.')
        return value

    def __repr__(self):
        return f'<Workout {self.id}: {self.title} (user_id={self.user_id})>'

"""User model for authentication and progress tracking.

This table stores registered users with a unique username and hashed
password.  Each user may have many submissions.  Passwords are
hashed using Werkzeug’s built‑in utilities.
"""

from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(db.Model, UserMixin):
    """User model for authentication and progress tracking.

    Incorporates Flask‑Login's ``UserMixin`` to provide the required
    attributes (``is_authenticated``, ``is_active``, ``is_anonymous``,
    ``get_id``) so that ``login_user()`` works without errors.  Users
    register with a unique username and hashed password.
    """

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    # Role field indicates whether the user is an educator, learner or both.
    # It controls permissions for quest creation.  Valid values are
    # 'educator', 'learner' and 'both'.  Default to 'learner' so
    # registrants without a selection still have a sensible role.
    role = db.Column(db.String(20), nullable=False, default='learner')

    # Relationship to submissions
    submissions = db.relationship('Submission', backref='user', lazy=True)

    def set_password(self, password: str) -> None:
        """Hash and store the user's password (PBKDF2)."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return True if the given password matches the stored hash."""
        if not self.password_hash:
            return False
        try:
            return check_password_hash(self.password_hash, password)
        except Exception:
            return False

    # ``get_id`` is provided by UserMixin, but we override it to
    # ensure the ID is returned as a string (Flask‑Login uses this
    # method internally).  Calling ``super().get_id()`` would return
    # ``id`` as an int, which still works, but returning a string is
    # explicit and mirrors earlier behaviour.
    def get_id(self) -> str:
        return str(self.id)

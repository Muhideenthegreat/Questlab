from app import db

# Import all models here for easy access
from app.models.quest import Quest, Task
from app.models.submission import Submission
from app.models.user import User

__all__ = ['Quest', 'Task', 'Submission', 'User']
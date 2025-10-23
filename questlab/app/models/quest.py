from app import db
from datetime import datetime
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Quest(db.Model):
    __tablename__ = 'quests'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    # Store tags as raw JSON text.  Using a Text column avoids
    # potential issues with SQLite’s limited JSON support and makes
    # migrations simpler.  When accessing or modifying the tags you
    # should convert between Python lists and JSON strings (see
    # QuestService for helpers).
    tags = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    published = db.Column(db.Boolean, default=False)
    
    # Relationship with tasks
    tasks = db.relationship('Task', backref='quest', lazy='dynamic', 
                          cascade='all, delete-orphan', order_by='Task.task_order')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            # Convert JSON string back into a Python list for external use.
            'tags': self._tags_to_list(),
            'created_at': self.created_at.isoformat(),
            'published': self.published,
            'task_count': self.tasks.count()
        }

    def _tags_to_list(self):
        """Return the tags field as a list.  Handles JSON parsing errors gracefully."""
        import json
        if not self.tags:
            return []
        try:
            return json.loads(self.tags)
        except Exception:
            # If tags is not valid JSON (e.g. a comma separated string),
            # split on commas instead.
            return [t.strip() for t in str(self.tags).split(',') if t.strip()]

    @property
    def tags_list(self):
        """Expose the quest tags as a list for template consumption.

        The `tags` field stores data as JSON text to remain database agnostic.
        When rendering in templates we need a Python list of tags; this
        property wraps `_tags_to_list()` for easy access and consistent
        behaviour across the application.
        """
        return self._tags_to_list()

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    quest_id = db.Column(db.String(36), db.ForeignKey('quests.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text)
    task_order = db.Column(db.Integer, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'prompt': self.prompt,
            'instructions': self.instructions,
            'task_order': self.task_order
        }
from app import db
from datetime import datetime
import uuid

class Submission(db.Model):
    __tablename__ = 'submissions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    quest_id = db.Column(db.String(36), nullable=False)
    task_id = db.Column(db.String(36), nullable=False)
    media_filename = db.Column(db.String(255))
    reflection_text = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Link to the user that submitted this evidence.  A submission
    # may be anonymous (user_id is NULL) in earlier versions of the app.
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'quest_id': self.quest_id,
            'task_id': self.task_id,
            'media_filename': self.media_filename,
            'reflection_text': self.reflection_text,
            'submitted_at': self.submitted_at.isoformat()
        }

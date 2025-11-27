from app import db
from app.models.submission import Submission
from app.utils.security import sanitize_input
import uuid

class SubmissionService:
    """Service for handling task submissions"""
    
    @staticmethod
    def create_submission(quest_id, task_id, media_filename, reflection_text, user_id=None):
        """
        Persist a new submission.

        A submission records the evidence (optional media file and
        reflection text) that a user provides for a given task.  If
        ``user_id`` is supplied the submission will be associated with
        that user.  Older anonymous submissions will have
        ``user_id=None``.

        :param quest_id: The ID of the parent quest
        :param task_id: The ID of the task being submitted
        :param media_filename: Name of the uploaded file on disk
        :param reflection_text: The user's reflection on the task
        :param user_id: (optional) ID of the submitting user
        :returns: The created Submission record
        """
        submission = Submission(
            quest_id=quest_id,
            task_id=task_id,
            user_id=user_id,
            media_filename=media_filename,
            reflection_text=sanitize_input(reflection_text)
        )
        db.session.add(submission)
        db.session.commit()
        return submission
    
    @staticmethod
    def get_submissions_by_quest(quest_id):
        return Submission.query.filter_by(quest_id=quest_id).all()

    @staticmethod
    def get_submissions_by_user(user_id):
        """Return all submissions made by a given user."""
        return Submission.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_submission(submission_id: str) -> Submission | None:
        """Return a submission by id."""
        return Submission.query.get(submission_id)

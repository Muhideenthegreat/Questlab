"""
Tests for submission creation and analysis feedback.

These tests cover the ``SubmissionService`` behaviours, ensuring that
submissions are persisted correctly and retrievable by quest or user,
as well as the basic keyword analysis provided by
``AnalysisService``.  Where appropriate, optional fields such as
``user_id`` are exercised.

To execute only this module run::

    pytest -q questlab/tests/test_submissions.py
"""

import pytest

from app.services.quest_service import QuestService
from app.services.submission_service import SubmissionService
from app.services.analysis_service import AnalysisService


class TestSubmissionLifecycle:
    """Verify that submissions can be created and queried."""

    def test_create_and_retrieve_submissions(self, app):
        """Submissions should be persisted and queryable by quest and user."""
        with app.app_context():
            # First create a quest with a single task
            quest = QuestService.create_quest({
                'title': 'Submission Test Quest',
                'description': 'Test quest for submissions',
                'tags': ['science'],
                'published': True,
                'tasks': [
                    {
                        'title': 'Test Task',
                        'prompt': 'Complete this test task',
                        'instructions': 'Test instructions',
                        'task_order': 0
                    }
                ]
            })
            task = quest.tasks.first()

            # Create two submissions: one anonymous and one associated with a user
            sub1 = SubmissionService.create_submission(
                quest_id=quest.id,
                task_id=task.id,
                media_filename='test1.jpg',
                reflection_text='I observed interesting phenomena during this task.',
                user_id=None
            )
            sub2 = SubmissionService.create_submission(
                quest_id=quest.id,
                task_id=task.id,
                media_filename='test2.jpg',
                reflection_text='Another reflection',
                user_id=1
            )
            # Basic field checks
            assert sub1.id and sub2.id
            assert sub1.quest_id == quest.id
            assert sub2.quest_id == quest.id
            assert sub1.user_id is None
            assert sub2.user_id == 1

            # Retrieve submissions by quest
            submissions_by_quest = SubmissionService.get_submissions_by_quest(quest.id)
            assert {s.id for s in submissions_by_quest} == {sub1.id, sub2.id}

            # Retrieve submissions by user
            submissions_by_user = SubmissionService.get_submissions_by_user(1)
            assert [s.id for s in submissions_by_user] == [sub2.id]


class TestAnalysisService:
    """Tests for the simple analysis feedback."""

    def test_analyze_submission_with_keywords(self):
        """Should recognise keywords associated with supplied quest tags."""
        feedback = AnalysisService.analyze_submission(
            'I observed energy transfer and motion in the swing set',
            ['physics', 'science']
        )
        lower = feedback.lower()
        assert 'great work' in lower
        # At least one of the expected keywords should be mentioned
        assert any(k in lower for k in ['energy', 'motion'])

    def test_analyze_submission_generic(self):
        """When no keywords are found a generic message should be returned."""
        feedback = AnalysisService.analyze_submission(
            'This task was interesting but I am not sure what it means.',
            ['biology']
        )
        assert feedback.lower().startswith('good reflection')

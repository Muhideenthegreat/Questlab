"""
Unit tests for the quest‑related service layer and model helpers.

These tests exercise the high‑level behaviours exposed by
``QuestService`` as well as properties on the ``Quest`` model such
as the tag handling.  They focus on the business logic rather than
the underlying Flask or SQLAlchemy integration so that they can
detect regressions in validation, sanitisation and filtering logic.

Usage:
    pytest -q questlab/tests/test_quests.py
"""

import json
import pytest

from app.services.quest_service import QuestService
from app.models.quest import Quest


class TestQuestCreation:
    """Test quest creation, validation and sanitisation."""

    def test_create_quest_valid_and_sanitised(self, app):
        """Ensure a valid quest and its tasks are created correctly.

        In addition to basic field population this test verifies that
        inputs containing characters such as ``<`` and ``>`` are
        sanitised by ``sanitize_input``.  It also confirms that tags
        are stored as JSON text and exposed as a list via the
        ``tags_list`` property.
        """
        with app.app_context():
            quest_data = {
                'title': '  <Test Quest>  ',
                'description': '<p>A test quest for science exploration</p>',
                'tags': ['Science', 'physics'],
                'published': True,
                'tasks': [
                    {
                        'title': '<Observe Motion>',
                        'prompt': '  Find objects in motion and describe their movement ',
                        'instructions': 'Look for <examples> in your environment',
                        'task_order': 0
                    }
                ]
            }
            quest = QuestService.create_quest(quest_data)

            # A primary key should be generated
            assert quest.id, "Quest id should be populated"
            # The title and description should have angle brackets stripped and whitespace trimmed
            # ``sanitize_input`` will remove only the angle brackets leaving ``p`` and ``/p`` markers intact.
            assert quest.title == 'Test Quest'
            assert quest.description == 'pA test quest for science exploration/p'

            # Tags are stored as JSON text on the model
            # ``quest.tags`` itself is a JSON encoded string
            assert isinstance(quest.tags, str)
            assert json.loads(quest.tags) == ['Science', 'physics']
            # The helper property exposes tags as a list (case preserved)
            assert quest.tags_list == ['Science', 'physics']

            # A single task should have been created
            tasks = quest.tasks.all()
            assert len(tasks) == 1
            task = tasks[0]
            # Task title and instructions are sanitised
            assert task.title == 'Observe Motion'
            assert task.instructions == 'Look for examples in your environment'
            assert task.task_order == 0

    def test_create_quest_skips_invalid_tasks(self, app):
        """Tasks with missing titles or prompts should be ignored."""
        with app.app_context():
            quest_data = {
                'title': 'Quest with Some Invalid Tasks',
                'description': 'Desc',
                'tags': [],
                'tasks': [
                    {
                        'title': 'Valid Task',
                        'prompt': 'Prompt A',
                        'instructions': 'Instructions A',
                        'task_order': 1
                    },
                    {
                        'title': '',  # Missing title
                        'prompt': 'Prompt B',
                        'instructions': 'Instructions B',
                        'task_order': 2
                    },
                    {
                        'title': 'Missing Prompt',
                        'prompt': '',  # Missing prompt
                        'instructions': 'Instructions C',
                        'task_order': 3
                    }
                ]
            }
            quest = QuestService.create_quest(quest_data)
            # Only the first (valid) task should be persisted
            assert quest.tasks.count() == 1
            assert quest.tasks.first().title == 'Valid Task'

    def test_create_quest_requires_title(self, app):
        """An empty or missing title should raise a ValueError."""
        with app.app_context():
            # Title missing entirely
            data_missing = {'description': 'No title'}
            with pytest.raises(ValueError):
                QuestService.create_quest(data_missing)
            # Title is blank after sanitisation
            data_blank = {'title': '<>', 'description': 'Blank title'}
            with pytest.raises(ValueError):
                QuestService.create_quest(data_blank)


class TestQuestRetrieval:
    """Tests for retrieving and filtering quests."""

    def test_get_published_quests_filtering(self, app):
        """Only published quests should be returned and filters should narrow the results."""
        with app.app_context():
            # Create a published quest with multiple tags
            q1 = QuestService.create_quest({
                'title': 'Physics Quest',
                'description': 'Physics content',
                'tags': ['physics', 'science'],
                'published': True,
                'tasks': []
            })
            # Create another published quest without the target tag
            q2 = QuestService.create_quest({
                'title': 'Biology Quest',
                'description': 'Biology content',
                'tags': ['biology'],
                'published': True,
                'tasks': []
            })
            # Draft quest should never appear
            QuestService.create_quest({
                'title': 'Chemistry Draft',
                'description': 'Not published',
                'tags': ['chemistry'],
                'published': False,
                'tasks': []
            })
            # Without filter we should see the two published quests
            all_published = QuestService.get_published_quests()
            assert {q.title for q in all_published} == {'Physics Quest', 'Biology Quest'}
            # Filter by a single tag (string)
            physics_only = QuestService.get_published_quests({'tags': 'physics'})
            assert [q.title for q in physics_only] == ['Physics Quest']
            # Filter by a list of tags
            multi_tag = QuestService.get_published_quests({'tags': ['biology', 'physics']})
            assert {q.title for q in multi_tag} == {'Physics Quest', 'Biology Quest'}

    def test_get_all_quests_order_and_get_by_id(self, app):
        """``get_all_quests`` should return quests in reverse chronological order.

        Also verify that ``get_quest_by_id`` returns the correct instance.
        """
        with app.app_context():
            # Create quests in sequence; later quests should appear first in the list
            q1 = QuestService.create_quest({'title': 'First', 'description': '', 'tags': [], 'tasks': []})
            q2 = QuestService.create_quest({'title': 'Second', 'description': '', 'tags': [], 'tasks': []})
            q3 = QuestService.create_quest({'title': 'Third', 'description': '', 'tags': [], 'tasks': []})
            all_quests = QuestService.get_all_quests()
            # The most recently created quest should be first
            assert all_quests[0].id == q3.id
            assert all_quests[1].id == q2.id
            assert all_quests[2].id == q1.id
            # Ensure ``get_quest_by_id`` retrieves the expected record
            retrieved = QuestService.get_quest_by_id(q2.id)
            assert retrieved.id == q2.id
            assert retrieved.title == 'Second'

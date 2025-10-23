from app import db
from app.models.quest import Quest, Task
from app.utils.security import sanitize_input
import json

class QuestService:
    """Service layer for quest operations"""
    
    @staticmethod
    def create_quest(quest_data):
        """
        Create a new quest along with its tasks.

        This method performs basic validation on the incoming data.  In
        particular it will ensure that a non-empty title is provided
        before attempting to persist anything to the database.  Tasks
        are optional; if provided they will be created in the order
        specified by ``task_order``.

        :param dict quest_data: Data describing the quest and its tasks.
        :raises ValueError: If a required field (e.g. title) is
          missing or empty.
        :returns Quest: The newly created quest instance.
        """
        title = sanitize_input(quest_data.get('title'))
        if not title:
            # Immediately bail out if no meaningful title was supplied.
            raise ValueError("Quest title is required")
        description = sanitize_input(quest_data.get('description'))
        raw_tags = quest_data.get('tags', []) or []
        # Convert the incoming list of tags into a JSON string for
        # storage.  Storing as JSON text avoids database type
        # mismatches on SQLite.  If tags is already a string, assume
        # it's JSON and leave it as is.
        if isinstance(raw_tags, str):
            tags_json = raw_tags
        else:
            try:
                tags_json = json.dumps(raw_tags)
            except Exception:
                tags_json = json.dumps([])
        published = quest_data.get('published', False)
        try:
            # Initialise and persist the quest itself
            quest = Quest(
                title=title,
                description=description,
                tags=tags_json,
                published=published
            )
            db.session.add(quest)
            # Flush the session so that quest.id is populated before
            # creating tasks.  Without flushing, the primary key default
            # may not be assigned and tasks would have a NULL quest_id.
            db.session.flush()
            # Create and persist any associated tasks
            for task_data in quest_data.get('tasks', []):
                task_title = sanitize_input(task_data.get('title'))
                task_prompt = sanitize_input(task_data.get('prompt'))
                # Skip creation if required task fields are missing
                if not task_title or not task_prompt:
                    continue
                task = Task(
                    quest_id=quest.id,
                    title=task_title,
                    prompt=task_prompt,
                    instructions=sanitize_input(task_data.get('instructions')),
                    task_order=task_data.get('task_order', 0)
                )
                db.session.add(task)
            db.session.commit()
            return quest
        except Exception as e:
            # Rollback to maintain transactional integrity then re-raise
            db.session.rollback()
            raise
    
    @staticmethod
    def get_published_quests(filters=None):
        """
        Return all quests that have been published.  Optionally filter
        by a tag.  Because SQLite has limited JSON support and we want
        predictable behaviour across databases, filtering by tag is
        performed in Python rather than relying on database-specific
        JSON operators.

        :param dict filters: Optional dictionary of filter
          parameters.  Supported key: ``tags`` – a comma separated
          string or list of tags.  Only quests containing at least
          one of these tags will be returned.
        :returns list[Quest]: Ordered list of published quests.
        """
        # Start by querying all published quests
        query = Quest.query.filter_by(published=True)
        quests = query.order_by(Quest.created_at.desc()).all()
        # If a tag filter was provided, normalise the requested tags and
        # perform in-memory filtering.  Because the Quest.tags field is
        # stored as JSON text, we convert it back into a list for
        # comparison.
        if filters and 'tags' in filters and filters['tags']:
            raw = filters['tags']
            if isinstance(raw, str):
                tag_list = [t.strip().lower() for t in raw.split(',') if t.strip()]
            elif isinstance(raw, (list, tuple)):
                tag_list = [str(t).strip().lower() for t in raw if str(t).strip()]
            else:
                tag_list = []
            if tag_list:
                import json
                filtered = []
                for q in quests:
                    if not q.tags:
                        continue
                    try:
                        q_tags = json.loads(q.tags)
                    except Exception:
                        q_tags = [t.strip() for t in str(q.tags).split(',') if t.strip()]
                    # Compare lowercased tags for intersection
                    if any(str(tag).lower() in tag_list for tag in q_tags):
                        filtered.append(q)
                quests = filtered
        return quests
    
    @staticmethod
    def get_quest_by_id(quest_id):
        return Quest.query.get(quest_id)
    
    @staticmethod
    def get_all_quests():
        return Quest.query.order_by(Quest.created_at.desc()).all()
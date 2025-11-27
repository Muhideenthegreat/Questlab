"""
One-time seeding script for local development only.

Usage:
    source venv/bin/activate
    DATABASE_URL=sqlite:///instance/questlab.db python seed.py

NEVER run this in production.
"""

from app import create_app, db
from app.models.user import User
from app.services.quest_service import QuestService


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='randomuser', role='educator')
            admin.set_password('Password123!')
            db.session.add(admin)

        if not QuestService.get_all_quests():
            QuestService.create_quest({
                'title': "Exploring Newton's Laws",
                'description': 'A series of physics tasks...',
                'tags': ['science', 'physics', 'energy'],
                'published': True,
                'tasks': [
                    {'title': 'Observe Motion', 'prompt': 'Find moving objects and describe forces', 'instructions': 'Use everyday examples', 'task_order': 0}
                ]
            })
            QuestService.create_quest({
                'title': 'Kitchen Microbiology',
                'description': 'Investigate the hidden world...',
                'tags': ['biology', 'microbiology', 'kitchen'],
                'published': True,
                'tasks': [
                    {'title': 'Grow Cultures', 'prompt': 'Observe growth patterns', 'instructions': 'Document daily', 'task_order': 0}
                ]
            })

        db.session.commit()
        print("Seed complete (admin/Password123! and sample quests)")


if __name__ == "__main__":
    main()

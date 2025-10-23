from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.services.quest_service import QuestService
from app import db

quest_bp = Blueprint('quest', __name__)

@quest_bp.route('/')
def gallery():
    """FR-002: Quest discovery and filtering"""
    tags_filter = request.args.get('tags')
    filters = {'tags': tags_filter} if tags_filter else None
    
    quests = QuestService.get_published_quests(filters)
    return render_template('gallery.html', quests=quests)

@quest_bp.route('/quest/<quest_id>')
def quest_detail(quest_id):
    """FR-002: Quest details view"""
    quest = QuestService.get_quest_by_id(quest_id)
    if not quest:
        flash('Quest not found', 'error')
        return redirect(url_for('quest.gallery'))
    
    return render_template('quest_detail.html', quest=quest)

@quest_bp.route('/quest/create', methods=['GET', 'POST'])
@login_required
def create_quest():
    """FR-001: Quest creation.

    Only users with the role ``educator`` or ``both`` may create quests.
    Learners are redirected to the gallery with an error message.
    """
    # Enforce role-based permission
    if current_user.role not in ('educator', 'both'):
        flash('You do not have permission to create quests.', 'error')
        return redirect(url_for('quest.gallery'))

    if request.method == 'POST':
        try:
            # Get form data
            title = request.form.get('title')
            description = request.form.get('description')
            tags = [tag.strip() for tag in request.form.get('tags', '').split(',') if tag.strip()]

            # Process tasks
            tasks = []
            task_count = int(request.form.get('task_count', 0))
            for i in range(task_count):
                task_title = request.form.get(f'task_title_{i}')
                task_prompt = request.form.get(f'task_prompt_{i}')
                task_instructions = request.form.get(f'task_instructions_{i}')
                if task_title and task_prompt:
                    tasks.append({
                        'title': task_title,
                        'prompt': task_prompt,
                        'instructions': task_instructions,
                        'task_order': i
                    })
            quest_data = {
                'title': title,
                'description': description,
                'tags': tags,
                'published': 'publish' in request.form,
                'tasks': tasks
            }
            quest = QuestService.create_quest(quest_data)
            flash('Quest created successfully!', 'success')
            return redirect(url_for('quest.quest_detail', quest_id=quest.id))
        except Exception as e:
            # Provide a more informative error message during quest creation.
            # In production you might want to log the exception instead of
            # flashing it directly to users.
            flash(f'Error creating quest: {e}', 'error')
    return render_template('create_quest.html')

@quest_bp.route('/api/quests')
def api_quests():
    """API endpoint for quests (for potential future use)"""
    quests = QuestService.get_published_quests()
    return jsonify([quest.to_dict() for quest in quests])
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.services.quest_service import QuestService
from app import db
from app.utils.security import sanitize_input, normalize_tags

quest_bp = Blueprint('quest', __name__)

@quest_bp.route('/')
def gallery():
    """FR-002: Quest discovery and filtering"""
    tags_filter = sanitize_input(request.args.get('tags', ''))
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
        current_app.logger.warning(
            "quest.create.denied user_id=%s role=%s ip=%s",
            getattr(current_user, 'id', 'anon'),
            getattr(current_user, 'role', 'unknown'),
            request.remote_addr or 'unknown'
        )
        flash('You do not have permission to create quests.', 'error')
        return redirect(url_for('quest.gallery'))

    if request.method == 'POST':
        ip_addr = request.remote_addr or 'unknown'
        try:
            # Get form data
            title = sanitize_input(request.form.get('title'))
            description = sanitize_input(request.form.get('description'))
            tags = normalize_tags(request.form.get('tags', ''))
            if not title:
                flash('Quest title is required.', 'error')
                current_app.logger.warning("quest.create.validation_failed user_id=%s ip=%s reason=missing_title", current_user.id, ip_addr)
                return render_template('create_quest.html')
            if len(title) > 200 or len(description) > 2000:
                flash('Title or description too long.', 'error')
                current_app.logger.warning("quest.create.validation_failed user_id=%s ip=%s reason=length_exceeded", current_user.id, ip_addr)
                return render_template('create_quest.html')

            # Process tasks
            tasks = []
            try:
                task_count = min(max(int(request.form.get('task_count', 0)), 0), 25)
            except ValueError:
                task_count = 0
                current_app.logger.warning("quest.create.validation_failed user_id=%s ip=%s reason=invalid_task_count", current_user.id, ip_addr)
            for i in range(task_count):
                task_title = sanitize_input(request.form.get(f'task_title_{i}'))
                task_prompt = sanitize_input(request.form.get(f'task_prompt_{i}'))
                task_instructions = sanitize_input(request.form.get(f'task_instructions_{i}'))
                if task_title and task_prompt:
                    if len(task_title) > 200 or len(task_prompt) > 2000:
                        current_app.logger.warning("quest.create.validation_failed user_id=%s ip=%s reason=task_length index=%s", current_user.id, ip_addr, i)
                        flash('Task fields are too long.', 'error')
                        return render_template('create_quest.html')
                    tasks.append({
                        'title': task_title,
                        'prompt': task_prompt,
                        'instructions': task_instructions,
                        'task_order': i
                    })
                else:
                    current_app.logger.warning(
                        "quest.create.invalid_task user_id=%s ip=%s index=%s",
                        current_user.id,
                        ip_addr,
                        i
                    )
            quest_data = {
                'title': title,
                'description': description,
                'tags': tags,
                'published': 'publish' in request.form,
                'tasks': tasks
            }
            quest = QuestService.create_quest(quest_data)
            current_app.logger.info("quest.create.success user_id=%s quest_id=%s ip=%s", current_user.id, quest.id, ip_addr)
            flash('Quest created successfully!', 'success')
            return redirect(url_for('quest.quest_detail', quest_id=quest.id))
        except Exception as e:
            current_app.logger.exception("quest.create.failed user_id=%s ip=%s", current_user.id, ip_addr)
            flash('An error occurred while creating the quest. Please try again.', 'error')
    return render_template('create_quest.html')

@quest_bp.route('/api/quests')
def api_quests():
    """API endpoint for quests (for potential future use)"""
    quests = QuestService.get_published_quests()
    return jsonify([quest.to_dict() for quest in quests])

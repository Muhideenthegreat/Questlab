from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.services.submission_service import SubmissionService
from app.services.file_service import FileService
from app.services.analysis_service import AnalysisService
from app.services.quest_service import QuestService
from app.utils.security import sanitize_input
import uuid

submission_bp = Blueprint('submission', __name__)

@submission_bp.route('/quest/<quest_id>/task/<task_id>/submit', methods=['GET', 'POST'])
@login_required
def submit_task(quest_id, task_id):
    """FR‑003: Task submission (requires login)."""
    quest = QuestService.get_quest_by_id(quest_id)
    if not quest:
        flash('Quest not found', 'error')
        return redirect(url_for('quest.gallery'))
    
    # Find the specific task
    task = None
    for t in quest.tasks:
        if t.id == task_id:
            task = t
            break
    
    if not task:
        flash('Task not found', 'error')
        return redirect(url_for('quest.quest_detail', quest_id=quest_id))
    
    if request.method == 'POST':
        try:
            # Handle file upload
            media_filename = None
            if 'media_file' in request.files:
                file = request.files['media_file']
                if file and file.filename != '':
                    if FileService.validate_file_size(file):
                        file_id = str(uuid.uuid4())
                        media_filename = FileService.save_uploaded_file(file, file_id)
                    else:
                        flash('File too large. Maximum size is 10MB.', 'error')
                        return render_template('task_submit.html', quest=quest, task=task)
            
            # Get reflection text; strip leading/trailing whitespace
            reflection_text = sanitize_input(request.form.get('reflection_text', '').strip())

            # Validate that a file was uploaded
            if not media_filename:
                flash('Please upload a media file for this task.', 'error')
                return render_template('task_submit.html', quest=quest, task=task)

            # Validate that reflection text is provided
            if not reflection_text:
                flash('Please provide your reflection for this task.', 'error')
                return render_template('task_submit.html', quest=quest, task=task)

            # Create submission
            submission = SubmissionService.create_submission(
                quest_id, task_id, media_filename, reflection_text, user_id=current_user.id
            )
            
            # Generate feedback
            feedback = AnalysisService.analyze_submission(reflection_text, quest.tags)
            
            flash('Task submitted successfully!', 'success')
            return render_template('submission_feedback.html', 
                                 quest=quest, task=task, submission=submission, feedback=feedback)
            
        except Exception as e:
            flash(f'Error submitting task: {str(e)}', 'error')
    
    return render_template('task_submit.html', quest=quest, task=task)

@submission_bp.route('/submissions/<quest_id>')
def view_submissions(quest_id):
    """View submissions for a quest"""
    submissions = SubmissionService.get_submissions_by_quest(quest_id)
    quest = QuestService.get_quest_by_id(quest_id)
    return render_template('view_submissions.html', quest=quest, submissions=submissions)


@submission_bp.route('/dashboard')
@login_required
def dashboard():
    """Display a simple dashboard of the current user's submissions."""
    submissions = SubmissionService.get_submissions_by_user(current_user.id)
    return render_template('dashboard.html', submissions=submissions)
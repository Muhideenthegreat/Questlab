from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, abort, send_from_directory
from flask_login import login_required, current_user
from app.services.submission_service import SubmissionService
from app.services.file_service import FileService
from app.services.analysis_service import AnalysisService
from app.services.quest_service import QuestService
from app.utils.security import sanitize_input
from app.utils.rate_limit import check_rate_limit
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
    ip_addr = request.remote_addr or 'unknown'
    user_agent = request.user_agent.string if request.user_agent else ''
    limit, window = current_app.config.get('UPLOAD_RATE_LIMIT', (30, 900))
    if not check_rate_limit(f"upload:{ip_addr}", limit, window):
        current_app.logger.warning("submission.rate_limited user_id=%s ip=%s ua=%s", current_user.id, ip_addr, user_agent)
        abort(429, description="Too many uploads. Please try again later.")
    
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
                        current_app.logger.warning("submission.file.too_large user_id=%s ip=%s", current_user.id, ip_addr)
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
            if len(reflection_text) > 5000:
                flash('Reflection is too long.', 'error')
                current_app.logger.warning("submission.reflection.too_long user_id=%s ip=%s", current_user.id, ip_addr)
                return render_template('task_submit.html', quest=quest, task=task)

            # Create submission
            submission = SubmissionService.create_submission(
                quest_id, task_id, media_filename, reflection_text, user_id=current_user.id
            )
            
            # Generate feedback
            feedback = AnalysisService.analyze_submission(reflection_text, quest.tags_list)
            current_app.logger.info(
                "submission.created user_id=%s quest_id=%s task_id=%s ip=%s",
                current_user.id, quest_id, task_id, ip_addr
            )
            flash('Task submitted successfully!', 'success')
            return render_template('submission_feedback.html', 
                                 quest=quest, task=task, submission=submission, feedback=feedback)
            
        except Exception as e:
            current_app.logger.exception("submission.failed user_id=%s quest_id=%s task_id=%s ip=%s", current_user.id, quest_id, task_id, ip_addr)
            flash('An error occurred while submitting your task. Please try again.', 'error')
    
    return render_template('task_submit.html', quest=quest, task=task)

@submission_bp.route('/submissions/<quest_id>')
@login_required
def view_submissions(quest_id):
    """View submissions for a quest"""
    if current_user.role not in ('educator', 'both'):
        flash('You do not have permission to view all submissions.', 'error')
        current_app.logger.warning(
            "submission.view.denied user_id=%s quest_id=%s role=%s",
            current_user.id, quest_id, current_user.role
        )
        return redirect(url_for('quest.gallery'))
    submissions = SubmissionService.get_submissions_by_quest(quest_id)
    quest = QuestService.get_quest_by_id(quest_id)
    if not quest:
        flash('Quest not found', 'error')
        current_app.logger.warning("submission.view.quest_missing user_id=%s quest_id=%s", current_user.id, quest_id)
        return redirect(url_for('quest.gallery'))
    current_app.logger.info("submission.view user_id=%s quest_id=%s count=%s", current_user.id, quest_id, len(submissions))
    return render_template('view_submissions.html', quest=quest, submissions=submissions)


@submission_bp.route('/dashboard')
@login_required
def dashboard():
    """Display a simple dashboard of the current user's submissions."""
    submissions = SubmissionService.get_submissions_by_user(current_user.id)
    current_app.logger.info("dashboard.view user_id=%s submissions=%s", current_user.id, len(submissions))
    return render_template('dashboard.html', submissions=submissions)


@submission_bp.route('/files/<submission_id>/download')
@login_required
def download_file(submission_id):
    """Secure file download with ownership/role checks."""
    submission = SubmissionService.get_submission(submission_id)
    if not submission:
        flash('Submission not found', 'error')
        current_app.logger.warning("download.denied reason=missing_submission user_id=%s submission_id=%s", current_user.id, submission_id)
        return redirect(url_for('submission.dashboard'))

    # Ownership or educator role required
    if submission.user_id != current_user.id and current_user.role not in ('educator', 'both'):
        current_app.logger.warning(
            "download.denied reason=authz user_id=%s submission_user_id=%s role=%s",
            current_user.id, submission.user_id, current_user.role
        )
        abort(403)

    try:
        upload_dir, safe_name = FileService.get_serving_path(submission.media_filename)
        current_app.logger.info(
            "download.allowed user_id=%s submission_id=%s file=%s",
            current_user.id, submission_id, safe_name
        )
        return send_from_directory(upload_dir, safe_name, as_attachment=True)
    except FileNotFoundError:
        current_app.logger.warning(
            "download.denied reason=file_missing user_id=%s submission_id=%s file=%s",
            current_user.id, submission_id, submission.media_filename
        )
        abort(404)

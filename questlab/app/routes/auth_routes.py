"""Routes for user authentication.

This blueprint provides registration, login and logout routes.  It
relies on Flask‑Login to handle session management.  Users can
register with a unique username and password, then log in to access
personalized features such as the progress dashboard.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, abort
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.utils.security import (
    sanitize_input,
    validate_username,
    validate_password_strength,
    validate_email,
)
from urllib.parse import urlparse, urljoin
from app.utils.rate_limit import check_rate_limit, record_failure
from app.utils.tokens import generate_reset_token, verify_reset_token


auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new user."""
    if request.method == 'POST':
        ip_addr = request.remote_addr or 'unknown'
        user_agent = request.user_agent.string if request.user_agent else ''
        limit, window = current_app.config.get('REGISTER_RATE_LIMIT', (10, 900))
        key = f"register:{ip_addr}"
        if not check_rate_limit(key, limit, window):
            current_app.logger.warning("auth.register.rate_limited ip=%s ua=%s", ip_addr, user_agent)
            abort(429, description="Too many registration attempts. Please try again later.")
        username = sanitize_input(request.form.get('username', '').strip())
        email = sanitize_input(request.form.get('email', '').strip())
        password = request.form.get('password', '').strip()
        role = request.form.get('role', '').strip().lower() or 'learner'
        # Basic validation
        allowed_roles = {'educator', 'learner', 'both'}
        user_valid, user_msg = validate_username(username)
        pwd_valid, pwd_msg = validate_password_strength(password)
        email_valid, email_msg = validate_email(email)
        if not user_valid:
            flash(user_msg, 'error')
            current_app.logger.warning("auth.register.invalid_username ip=%s reason=%s", ip_addr, user_msg)
        elif not email_valid:
            flash(email_msg, 'error')
            current_app.logger.warning("auth.register.invalid_email ip=%s reason=%s", ip_addr, email_msg)
        elif not pwd_valid:
            flash(pwd_msg, 'error')
            current_app.logger.warning("auth.register.weak_password user=%s ip=%s reason=%s", username, ip_addr, pwd_msg)
        elif role not in allowed_roles:
            flash('Please select a valid role.', 'error')
            current_app.logger.warning("auth.register.invalid_role user=%s ip=%s role=%s", username, ip_addr, role)
        elif User.query.filter_by(username=username).first():
            flash('That username is already taken.', 'error')
            current_app.logger.warning("auth.register.duplicate user=%s ip=%s", username, ip_addr)
        elif User.query.filter_by(email=email).first():
            flash('That email is already registered.', 'error')
            current_app.logger.warning("auth.register.duplicate_email email=%s ip=%s", email, ip_addr)
        else:
            user = User(username=username, email=email, role=role)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            current_app.logger.info("auth.register.success user_id=%s role=%s ip=%s", user.id, role, ip_addr)
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Log in an existing user."""
    if request.method == 'POST':
        ip_addr = request.remote_addr or 'unknown'
        user_agent = request.user_agent.string if request.user_agent else ''
        limit, window = current_app.config.get('LOGIN_RATE_LIMIT', (5, 900))
        key = f"login:{ip_addr}"
        if not check_rate_limit(key, limit, window):
            current_app.logger.warning("auth.login.rate_limited ip=%s ua=%s", ip_addr, user_agent)
            abort(429, description="Too many login attempts. Please try again later.")
        username = sanitize_input(request.form.get('username', '').strip())
        password = request.form.get('password', '').strip()
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session.clear()  # drop any existing session state to prevent fixation
            login_user(user)
            current_app.logger.info("auth.login.success user_id=%s ip=%s", user.id, ip_addr)
            flash('Welcome back!', 'success')
            next_page = request.args.get('next')
            if next_page and _is_safe_redirect(next_page):
                return redirect(next_page)
            return redirect(url_for('quest.gallery'))
        else:
            flash('Invalid username or password.', 'error')
            count = record_failure(f"auth_fail:{ip_addr}:{username}", window=window)
            current_app.logger.warning("auth.login.failure username=%s ip=%s attempts_in_window=%s", username or 'missing', ip_addr, count)
    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    current_app.logger.info("auth.logout user_id=%s", getattr(current_user, 'id', 'anon'))
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('quest.gallery'))


@auth_bp.route('/account/2fa', methods=['GET', 'POST'])
@login_required
def enable_2fa():
    """Placeholder - 2FA disabled."""
    flash('Two-factor authentication is currently unavailable.', 'info')
    return redirect(url_for('quest.gallery'))


@auth_bp.route('/reset', methods=['GET', 'POST'])
def reset_request():
    """Request a password reset token (email-based)."""
    if request.method == 'POST':
        email = sanitize_input(request.form.get('email', '').strip())
        user = User.query.filter_by(email=email).first()
        # Always respond generically
        flash('If that account exists, a reset link has been sent.', 'info')
        if user:
            token = generate_reset_token(user.id)
            _send_reset_email(user.email, token)
            current_app.logger.info("auth.reset.request user_id=%s ip=%s", user.id, request.remote_addr or 'unknown')
        return redirect(url_for('auth.login'))
    return render_template('auth/reset_request.html')


@auth_bp.route('/reset/<token>', methods=['GET', 'POST'])
def reset_with_token(token):
    """Reset password using a signed token."""
    user_id = verify_reset_token(token)
    if not user_id:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('auth.reset_request'))

    user = User.query.get(user_id)
    if not user:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('auth.reset_request'))

    if request.method == 'POST':
        new_password = request.form.get('password', '').strip()
        valid, msg = validate_password_strength(new_password)
        if not valid:
            flash(msg, 'error')
            return render_template('auth/reset_password.html', token=token)
        user.set_password(new_password)
        db.session.commit()
        current_app.logger.info("auth.reset.success user_id=%s ip=%s", user.id, request.remote_addr or 'unknown')
        flash('Password updated. Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)


def _send_reset_email(recipient: str, token: str) -> None:
    """Send a reset email or log the link if mail not configured."""
    reset_link = url_for('auth.reset_with_token', token=token, _external=True)
    server = current_app.config.get('MAIL_SERVER')
    sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME')
    if not server or not sender:
        current_app.logger.info("auth.reset.email_link recipient=%s link=%s", recipient, reset_link)
        return

    import smtplib
    from email.message import EmailMessage

    msg = EmailMessage()
    msg['Subject'] = 'QuestLab Password Reset'
    msg['From'] = sender
    msg['To'] = recipient
    msg.set_content(f"Use the link below to reset your password:\n\n{reset_link}\n\nIf you did not request this, ignore this email.")

    try:
        port = current_app.config.get('MAIL_PORT', 587)
        use_tls = current_app.config.get('MAIL_USE_TLS', True)
        username = current_app.config.get('MAIL_USERNAME')
        password = current_app.config.get('MAIL_PASSWORD')

        with smtplib.SMTP(server, port) as smtp:
            if use_tls:
                smtp.starttls()
            if username and password:
                smtp.login(username, password)
            smtp.send_message(msg)
        current_app.logger.info("auth.reset.email_sent recipient=%s", recipient)
    except Exception as e:
        current_app.logger.exception("auth.reset.email_failed recipient=%s error=%s", recipient, e)
        # As fallback, log the link
        current_app.logger.info("auth.reset.email_link recipient=%s link=%s", recipient, reset_link)


def _is_safe_redirect(target: str) -> bool:
    """Prevent open redirect vulnerabilities by validating the target URL."""
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return (
        test_url.scheme in ('http', 'https')
        and ref_url.netloc == test_url.netloc
    )

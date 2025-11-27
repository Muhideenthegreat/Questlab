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
)
from urllib.parse import urlparse, urljoin
from app.utils.rate_limit import check_rate_limit, record_failure


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
        password = request.form.get('password', '').strip()
        role = request.form.get('role', '').strip().lower() or 'learner'
        # Basic validation
        allowed_roles = {'educator', 'learner', 'both'}
        user_valid, user_msg = validate_username(username)
        pwd_valid, pwd_msg = validate_password_strength(password)
        if not user_valid:
            flash(user_msg, 'error')
            current_app.logger.warning("auth.register.invalid_username ip=%s reason=%s", ip_addr, user_msg)
        elif not pwd_valid:
            flash(pwd_msg, 'error')
            current_app.logger.warning("auth.register.weak_password user=%s ip=%s reason=%s", username, ip_addr, pwd_msg)
        elif role not in allowed_roles:
            flash('Please select a valid role.', 'error')
            current_app.logger.warning("auth.register.invalid_role user=%s ip=%s role=%s", username, ip_addr, role)
        elif User.query.filter_by(username=username).first():
            flash('That username is already taken.', 'error')
            current_app.logger.warning("auth.register.duplicate user=%s ip=%s", username, ip_addr)
        else:
            user = User(username=username, role=role)
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

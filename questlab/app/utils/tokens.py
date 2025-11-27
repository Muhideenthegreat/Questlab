"""Token helpers for time-limited password reset links."""

from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app


def _serializer():
    secret = current_app.config['SECRET_KEY']
    return URLSafeTimedSerializer(secret_key=secret, salt='questlab-reset')


def generate_reset_token(user_id: int) -> str:
    """Return a signed token encoding the user id."""
    return _serializer().dumps({'uid': user_id})


def verify_reset_token(token: str, max_age: int = 3600):
    """Return the user id if the token is valid and not expired."""
    try:
        data = _serializer().loads(token, max_age=max_age)
        return data.get('uid')
    except (BadSignature, SignatureExpired):
        return None

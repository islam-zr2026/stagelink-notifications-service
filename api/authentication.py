"""Authentication classes for the notifications service.

DevHeaderAuthentication is a TEMPORARY, development-only stub (build step 2).
It is replaced by real JWT validation in build step 3.
"""
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

USER_ID_HEADER = "HTTP_X_USER_ID"


class StatelessUser:
    """Lightweight user built from request data; there is no local User table."""

    is_authenticated = True

    def __init__(self, user_id, role=None):
        self.id = user_id
        self.role = role


class DevHeaderAuthentication(BaseAuthentication):
    """DEV ONLY: trust the X-User-Id header when DEV_AUTH_ENABLED is true."""

    def authenticate(self, request):
        if not settings.DEV_AUTH_ENABLED:
            return None

        raw_user_id = request.META.get(USER_ID_HEADER)
        if raw_user_id is None:
            return None

        try:
            user_id = int(raw_user_id)
        except ValueError:
            raise AuthenticationFailed("X-User-Id must be an integer.")

        return (StatelessUser(user_id), None)

    def authenticate_header(self, request):
        return "X-User-Id"

from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
import pdb

class AuthHeaderMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        authorization = request.META.get("HTTP_AUTHORIZATION")
        if not authorization:
            response = self.get_response(request)
            return response
        request.user = User.objects.get(
            id = SessionStore(session_key = authorization).get('_auth_user_id')
        )
        response = self.get_response(request)
        return response

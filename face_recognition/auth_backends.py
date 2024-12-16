# myapp/auth_backends.py

from django.contrib.auth.backends import BaseBackend
from .models import User
from django.core.exceptions import ObjectDoesNotExist

class CustomAuthenticationBackend(BaseBackend):
    def authenticate(self, request, username=None, identity_number=None, password=None, **kwargs):
        try:
            # Check if the user exists with the provided username and identity_number
            user = User.objects.get(username=username, identity_number=identity_number)
            
            # Check if the password is correct
            if user.check_password(password):
                return user
            else:
                return None
        except ObjectDoesNotExist:
            return None

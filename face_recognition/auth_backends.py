# myapp/auth_backends.py

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

class IdentityNumberBackend(BaseBackend):
    def authenticate(self, request, username=None, identity_number=None, password=None, **kwargs):
        try:
            # Check if the user exists with the provided username and identity_number
            user = User.objects.get(username=username, profile__identity_number=identity_number)
            
            # Check if the password is correct
            if user.check_password(password):
                return user
            else:
                return None
        except ObjectDoesNotExist:
            return None

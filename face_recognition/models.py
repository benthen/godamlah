from django.db import models
from django.contrib.auth.hashers import make_password

class User(models.Model):
    username = models.CharField(max_length=100, unique=True, default="")
    identity_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(default="")
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    typing_speed = models.FloatField(null=True, blank=True)
    device_type = models.CharField(max_length=50, null=True, blank=True)
    geolocation = models.CharField(max_length=100, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    password = models.CharField(max_length=100, default="")
        
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('$'):
            # Hash the password if it isn't already hashed
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

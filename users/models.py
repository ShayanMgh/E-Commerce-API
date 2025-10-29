from django.contrib.auth.models import AbstractUser
from django.db import models
from .managers import UserManager

class User(AbstractUser):
    """
    Custom user using email as the unique identifier.
    Removes username; keeps first_name/last_name.
    """
    username = None
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # Email & password are required by default

    objects = UserManager()

    def __str__(self):
        return self.email

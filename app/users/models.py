from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserType(models.IntegerChoices):
    LIBRARY = 0, 'LIBRARY USER'
    VISITOR = 1, 'VISITOR USER'


class UserManager(BaseUserManager):
    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        extra_fields.setdefault('is_active', False)
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.update(user_type=UserType.LIBRARY, is_staff=True, is_superuser=True, is_active=True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    user_type = models.SmallIntegerField(choices=UserType.choices)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

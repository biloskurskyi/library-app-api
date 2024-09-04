from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields['user_type'] = 0

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        extra_fields.pop('username', None)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    LIBRARY_USER = 0
    VISITOR_USER = 1
    USER_TYPE_CHOICES = ((LIBRARY_USER, 'LIBRARY USER'), (VISITOR_USER, 'VISITOR USER'),)
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    user_type = models.SmallIntegerField(choices=USER_TYPE_CHOICES)
    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        if self.user_type == self.LIBRARY_USER:
            return f"{self.name} with email {self.email} (Library User)"
        elif self.user_type == self.VISITOR_USER:
            return f"{self.name} with email {self.email} (Visitor User)"

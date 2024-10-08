import re
from datetime import timedelta

from decouple import config
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from app import settings


class UserManager(BaseUserManager):
    """
    Custom manager for the User model.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and return a regular user with an email and password.
        """
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and return a superuser with an email and password.
        """
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
    """
    Custom User model for the application.
    """
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

    def set_password(self, raw_password):
        """
        Set the password for the user after validating its strength.
        """
        if len(raw_password) < int(config('PASSWORD_LENGTH')):
            raise ValidationError("Password must be at least 8 characters long.")
        if not re.search(r'[A-Z]', raw_password):
            raise ValidationError("Password must contain at least one uppercase letter.")

        super().set_password(raw_password)


class Book(models.Model):
    """
    Model representing a book in the library.
    """
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    total_copies = models.PositiveIntegerField()
    available_copies = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        ordering = ['title']
        unique_together = ('title', 'author')

    def __str__(self):
        return f'{self.title} by {self.author}'


class BorrowRecord(models.Model):
    """
    Model representing a record of a book borrowed by a user.
    """
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Borrow Record'
        verbose_name_plural = 'Borrow Records'
        ordering = ['borrowed_at']

    def save(self, *args, **kwargs):
        """
        Save the borrow record, setting the due date if not provided.
        """
        if not self.pk and self.due_date is None:
            if self.borrowed_at is None:
                self.borrowed_at = timezone.now()
            self.due_date = self.borrowed_at + timedelta(days=30)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.book.title} borrowed by {self.member} on {self.borrowed_at}'

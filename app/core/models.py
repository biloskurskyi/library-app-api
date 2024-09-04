from datetime import timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone

from app import settings


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


class Book(models.Model):
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
        # Якщо об'єкт новий і due_date не встановлено
        if not self.pk and self.due_date is None:
            if self.borrowed_at is None:
                self.borrowed_at = timezone.now()
            self.due_date = self.borrowed_at + timedelta(days=30)
        super().save(*args, **kwargs)

    def is_overdue(self):
        return self.due_date < timezone.now() and self.returned_at is None

    def __str__(self):
        return f'{self.book.title} borrowed by {self.member} on {self.borrowed_at}'

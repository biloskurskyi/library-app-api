from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from books.models import Book


def default_due_date():
    return timezone.now() + timedelta(days=30)


class Loan(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='loans')
    member = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='loans')
    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(default=default_due_date)
    returned_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['borrowed_at']
        constraints = [
            models.UniqueConstraint(
                fields=['book', 'member'],
                condition=models.Q(returned_at__isnull=True),
                name='unique_active_loan',
            ),
        ]

    def __str__(self):
        return f'{self.book} / {self.member}'

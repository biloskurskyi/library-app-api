from django.db import models


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    total_copies = models.PositiveIntegerField()
    available_copies = models.PositiveIntegerField()

    class Meta:
        ordering = ['title']
        constraints = [
            models.UniqueConstraint(fields=['title', 'author'], name='unique_book_title_author'),
        ]

    def __str__(self):
        return self.title

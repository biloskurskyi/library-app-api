from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from .models import Book


def update(book_id, data):
    with transaction.atomic():
        book = get_object_or_404(Book.objects.select_for_update(), pk=book_id)
        total_copies = data.pop('total_copies', None)
        for field, value in data.items():
            setattr(book, field, value)
        if total_copies is not None:
            if total_copies < book.available_copies:
                total_copies = book.available_copies
            elif total_copies > book.total_copies:
                book.available_copies += total_copies - book.total_copies
            book.total_copies = total_copies
        book.save()
        return book


def destroy(book_id):
    with transaction.atomic():
        book = get_object_or_404(Book.objects.select_for_update(), pk=book_id)
        if book.available_copies != book.total_copies:
            raise ValidationError('Cannot delete the book because some copies are currently borrowed.')
        book.delete()

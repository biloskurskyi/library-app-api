from django.db import IntegrityError
from django.test import TestCase

from books.models import Book


class BookTests(TestCase):
    def test_duplicate_title_author_rejected(self):
        Book.objects.create(title='Dune', author='Frank Herbert', total_copies=3, available_copies=3)
        with self.assertRaises(IntegrityError):
            Book.objects.create(title='Dune', author='Frank Herbert', total_copies=1, available_copies=1)

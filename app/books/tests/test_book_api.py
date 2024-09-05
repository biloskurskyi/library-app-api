from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from core.models import Book, User
from user.tests.test_user_api import UserApiTestsBase


class BooksApiTestsBase(UserApiTestsBase, TestCase):
    """Base class for book-related API tests."""

    def setUp(self):
        super().setUp()
        self.books_url = reverse('books:books-info')

    def add_book(self, **kwargs):
        """Helper method to add a book."""
        data = {
            'title': 'Test Book',
            'author': 'Test Author',
            'total_copies': '11',
            'available_copies': '11',
        }
        data.update(kwargs)
        return self.client.post(self.books_url, data, format='json')

    def get_books(self):
        """Helper method to get all books."""
        return self.client.get(self.books_url)


class BooksApiTests(BooksApiTestsBase):
    """Tests for the Books API."""

    @patch('user.tasks.send_activation_email.delay')
    def test_add_book_success(self, mock_send_activation_email):
        """Ensure a library user can add a book."""
        mock_send_activation_email.return_value = None
        self.register_user()

        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.save()

        self.get_token()  # token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token()}')
        response = self.add_book()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('title', response.data)
        self.assertEqual(response.data['title'], 'Test Book')

    @patch('user.tasks.send_activation_email.delay')
    def test_get_books_success(self, mock_send_activation_email):
        """Ensure all books are retrieved successfully."""
        mock_send_activation_email.return_value = None
        self.register_user()

        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.save()

        self.get_token()  # token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.get_token()}')
        response = self.get_books()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

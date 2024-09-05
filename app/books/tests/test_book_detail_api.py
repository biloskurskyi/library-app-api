from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from core.models import Book, User
from user.tests.test_user_api import UserApiTestsBase


class BookDetailApiTests(UserApiTestsBase, TestCase):
    """Tests for the Book Detail API."""

    def get_book_url(self, book_id):
        """Helper method to get the book detail URL."""
        return reverse('books:book-detail', args=[book_id])

    def add_book_to_db(self):
        """Helper method to add a book to the database directly."""
        book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            total_copies=11,
            available_copies=11
        )
        return book

    @patch('user.tasks.send_activation_email.delay')
    def test_get_book_success(self, mock_send_activation_email):
        """Ensure a user can get book details."""
        mock_send_activation_email.return_value = None
        self.register_user()

        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.save()

        token = self.get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        book = self.add_book_to_db()
        response = self.client.get(self.get_book_url(book.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('title', response.data)
        self.assertEqual(response.data['title'], book.title)

    @patch('user.tasks.send_activation_email.delay')
    def test_get_book_not_found(self, mock_send_activation_email):
        """Ensure getting a book that doesn't exist returns 404."""
        mock_send_activation_email.return_value = None
        self.register_user()

        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.save()

        token = self.get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.client.get(self.get_book_url(999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('user.tasks.send_activation_email.delay')
    def test_update_book_success(self, mock_send_activation_email):
        """Ensure a library user can update book details."""
        mock_send_activation_email.return_value = None
        self.register_user()

        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.save()

        token = self.get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        book = self.add_book_to_db()
        update_data = {'title': 'Updated Title'}

        response = self.client.patch(self.get_book_url(book.id), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Updated Title')

    @patch('user.tasks.send_activation_email.delay')
    def test_update_book_forbidden(self, mock_send_activation_email):
        """Ensure non-library users cannot update book details."""
        mock_send_activation_email.return_value = None
        self.register_user(user_type=1)

        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.save()

        token = self.get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        book = self.add_book_to_db()
        update_data = {'title': 'Updated Title'}

        response = self.client.patch(self.get_book_url(book.id), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('user.tasks.send_activation_email.delay')
    def test_delete_book_success(self, mock_send_activation_email):
        """Ensure a library user can delete a book."""
        mock_send_activation_email.return_value = None
        self.register_user()

        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.save()

        token = self.get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        book = self.add_book_to_db()
        response = self.client.delete(self.get_book_url(book.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    @patch('user.tasks.send_activation_email.delay')
    def test_delete_book_with_borrowed_copies(self, mock_send_activation_email):
        """Ensure a book cannot be deleted if some copies are borrowed."""
        mock_send_activation_email.return_value = None
        self.register_user()

        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.save()

        token = self.get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        book = Book.objects.create(
            title='Test Book',
            author='Test Author',
            total_copies=11,
            available_copies=5
        )

        response = self.client.delete(self.get_book_url(book.id))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Cannot delete the book because some copies are currently borrowed.')

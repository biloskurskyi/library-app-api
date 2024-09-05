from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from core.models import Book, BorrowRecord, User
from user.tests.test_user_api import UserApiTestsBase


class BorrowBookApiTestsBase(UserApiTestsBase, TestCase):
    """Base class for borrowing-related API tests."""

    def setUp(self):
        super().setUp()
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            total_copies=5,
            available_copies=5
        )
        self.borrow_url = reverse('borrow:borrow-book', kwargs={'pk': self.book.id})
        self.return_url = reverse('borrow:return-book', kwargs={'pk': self.book.id})

    def borrow_book(self):
        """Helper method to borrow a book."""
        return self.client.post(self.borrow_url, format='json')

    def return_book(self):
        """Helper method to return a book."""
        return self.client.post(self.return_url, format='json')


class BorrowBookApiTests(BorrowBookApiTestsBase):
    """Tests for borrowing and returning books."""

    @patch('user.tasks.send_activation_email.delay')
    @patch('borrow.tasks.send_notification_email.delay')
    def test_borrow_book_success(self, mock_send_notification_email, mock_send_activation_email):
        """Test that a visitor user can borrow a book successfully."""
        mock_send_notification_email.return_value = None
        mock_send_activation_email.return_value = None
        self.register_user()

        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.user_type = User.VISITOR_USER
        user.save()

        token = self.get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.borrow_book()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 4)

    @patch('user.tasks.send_activation_email.delay')
    @patch('borrow.tasks.send_notification_email.delay')
    def test_borrow_book_already_borrowed(self, mock_send_notification_email, mock_send_activation_email):
        """Test that a user cannot borrow the same book twice."""
        mock_send_notification_email.return_value = None
        mock_send_activation_email.side_effect = None
        self.register_user()

        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.user_type = User.VISITOR_USER
        user.save()

        token = self.get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        self.borrow_book()

        response = self.borrow_book()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'You have already borrowed this book.')

    @patch('user.tasks.send_activation_email.delay')
    @patch('borrow.tasks.send_notification_email.delay')
    def test_return_book_success(self, mock_send_notification_email, mock_send_activation_email):
        """Test that a user can successfully return a borrowed book."""
        mock_send_notification_email.return_value = None
        mock_send_activation_email.side_effect = None
        self.register_user()

        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.user_type = User.VISITOR_USER
        user.save()

        token = self.get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        self.borrow_book()

        response = self.return_book()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 5)

    @patch('user.tasks.send_activation_email.delay')
    @patch('borrow.tasks.send_overdue_notifications.delay')
    def test_return_book_not_borrowed(self, mock_send_notification_email, mock_send_overdue_notifications):
        """Test that a user cannot return a book they haven't borrowed."""
        mock_send_notification_email.return_value = None
        mock_send_overdue_notifications.return_value = None
        self.register_user()

        user = User.objects.get(email=self.user_data['email'])
        user.is_active = True
        user.user_type = User.VISITOR_USER
        user.save()

        token = self.get_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        response = self.return_book()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'No record found for this book or you have already returned it.')

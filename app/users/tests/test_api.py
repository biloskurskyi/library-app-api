import time
from unittest import mock

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from books.models import Book
from borrowing.models import Loan
from users import services
from users.models import UserType


def create_user(email='visitor@example.com', user_type=UserType.VISITOR, is_active=True, name='Visitor'):
    return get_user_model().objects.create_user(
        email=email,
        password='Password1',
        name=name,
        user_type=user_type,
        is_active=is_active,
    )


class RegisterApiTests(APITestCase):
    @mock.patch('users.services.send_activation_email.delay')
    def test_register_creates_inactive_visitor(self, mock_delay):
        payload = {
            'name': 'Visitor',
            'email': 'Visitor@EXAMPLE.com',
            'password': 'Password1',
            'user_type': UserType.LIBRARY,
        }
        res = self.client.post('/api/users/', payload)
        self.assertEqual(res.status_code, 201)
        user = get_user_model().objects.get(pk=res.data['id'])
        self.assertEqual(res.data, {
            'id': user.id,
            'name': 'Visitor',
            'email': 'Visitor@example.com',
            'user_type': UserType.VISITOR,
        })
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password('Password1'))
        email, name, token = mock_delay.call_args.args
        self.assertEqual(email, user.email)
        self.assertEqual(name, user.name)
        self.assertIn(str(user.pk), token)

    @mock.patch('users.services.send_activation_email.delay')
    def test_register_blank_name_fails(self, mock_delay):
        res = self.client.post('/api/users/', {'name': '', 'email': 'v@example.com', 'password': 'Password1'})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['code'], 'VALIDATION_ERROR')
        self.assertFalse(get_user_model().objects.exists())
        mock_delay.assert_not_called()

    def test_register_duplicate_email_fails(self):
        create_user()
        res = self.client.post(
            '/api/users/',
            {'name': 'Visitor', 'email': 'visitor@example.com', 'password': 'Password1'},
        )
        self.assertEqual(res.status_code, 400)

    def test_register_short_password_fails(self):
        res = self.client.post('/api/users/', {'name': 'Visitor', 'email': 'v@example.com', 'password': 'Pass1'})
        self.assertEqual(res.status_code, 400)

    def test_register_password_without_uppercase_fails(self):
        res = self.client.post('/api/users/', {'name': 'Visitor', 'email': 'v@example.com', 'password': 'password1'})
        self.assertEqual(res.status_code, 400)


class ActivationApiTests(APITestCase):
    def test_activate(self):
        user = create_user(is_active=False)
        res = self.client.get(f'/api/activate/{services.activation_token(user)}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['detail'], 'User activated successfully.')
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_activate_already_active(self):
        user = create_user()
        res = self.client.get(f'/api/activate/{services.activation_token(user)}/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['detail'], 'User is active.')

    def test_activate_invalid_token(self):
        res = self.client.get('/api/activate/1:garbage:signature/')
        self.assertEqual(res.status_code, 400)

    def test_activate_expired_token(self):
        user = create_user(is_active=False)
        token = services.activation_token(user)
        with mock.patch('django.core.signing.time.time', return_value=time.time() + 4 * 86400):
            res = self.client.get(f'/api/activate/{token}/')
        self.assertEqual(res.status_code, 400)
        user.refresh_from_db()
        self.assertFalse(user.is_active)


class LoginApiTests(APITestCase):
    def test_login(self):
        user = create_user()
        res = self.client.post('/api/login/', {'email': 'visitor@example.com', 'password': 'Password1'})
        self.assertEqual(res.status_code, 200)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)
        self.assertEqual(res.data['id'], user.id)
        self.assertEqual(res.data['user_type'], UserType.VISITOR)

    def test_login_case_insensitive_email(self):
        create_user()
        res = self.client.post('/api/login/', {'email': 'VISITOR@example.com', 'password': 'Password1'})
        self.assertEqual(res.status_code, 200)

    def test_login_unactivated_fails(self):
        create_user(is_active=False)
        res = self.client.post('/api/login/', {'email': 'visitor@example.com', 'password': 'Password1'})
        self.assertEqual(res.status_code, 401)

    def test_login_wrong_password_fails(self):
        create_user()
        res = self.client.post('/api/login/', {'email': 'visitor@example.com', 'password': 'Wrong1234'})
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.data['code'], 'AUTHENTICATION_FAILED')

    def test_login_missing_fields_fails(self):
        res = self.client.post('/api/login/', {'email': 'visitor@example.com'})
        self.assertEqual(res.status_code, 400)


class LogoutApiTests(APITestCase):
    def test_logout_blacklists_refresh_token(self):
        create_user()
        login = self.client.post('/api/login/', {'email': 'visitor@example.com', 'password': 'Password1'})
        refresh = login.data['refresh']
        res = self.client.post('/api/logout/', {'refresh': refresh})
        self.assertEqual(res.status_code, 200)
        res = self.client.post('/api/logout/', {'refresh': refresh})
        self.assertEqual(res.status_code, 401)


class UserDestroyApiTests(APITestCase):
    def setUp(self):
        self.staff = create_user(email='staff@example.com', user_type=UserType.LIBRARY, name='Staff')

    def test_destroy_requires_authentication(self):
        res = self.client.delete(f'/api/users/{self.staff.pk}/')
        self.assertEqual(res.status_code, 401)

    def test_destroy_by_visitor_fails(self):
        visitor = create_user()
        self.client.force_authenticate(visitor)
        res = self.client.delete(f'/api/users/{visitor.pk}/')
        self.assertEqual(res.status_code, 403)

    def test_destroy_self(self):
        self.client.force_authenticate(self.staff)
        res = self.client.delete(f'/api/users/{self.staff.pk}/')
        self.assertEqual(res.status_code, 204)
        self.assertFalse(get_user_model().objects.filter(pk=self.staff.pk).exists())

    def test_destroy_visitor(self):
        visitor = create_user()
        self.client.force_authenticate(self.staff)
        res = self.client.delete(f'/api/users/{visitor.pk}/')
        self.assertEqual(res.status_code, 204)
        self.assertFalse(get_user_model().objects.filter(pk=visitor.pk).exists())

    def test_destroy_other_staff_fails(self):
        other = create_user(email='other@example.com', user_type=UserType.LIBRARY, name='Other')
        self.client.force_authenticate(self.staff)
        res = self.client.delete(f'/api/users/{other.pk}/')
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data['code'], 'PERMISSION_DENIED')

    def test_destroy_missing_user_fails(self):
        self.client.force_authenticate(self.staff)
        res = self.client.delete('/api/users/999/')
        self.assertEqual(res.status_code, 404)

    def test_destroy_visitor_with_active_loan_fails(self):
        visitor = create_user()
        book = Book.objects.create(title='Title', author='Author', total_copies=1, available_copies=0)
        Loan.objects.create(book=book, member=visitor)
        self.client.force_authenticate(self.staff)
        res = self.client.delete(f'/api/users/{visitor.pk}/')
        self.assertEqual(res.status_code, 403)
        self.assertTrue(get_user_model().objects.filter(pk=visitor.pk).exists())

    def test_destroy_self_with_active_loan_fails(self):
        book = Book.objects.create(title='Title', author='Author', total_copies=1, available_copies=0)
        Loan.objects.create(book=book, member=self.staff)
        self.client.force_authenticate(self.staff)
        res = self.client.delete(f'/api/users/{self.staff.pk}/')
        self.assertEqual(res.status_code, 403)

    def test_destroy_visitor_with_returned_loan(self):
        visitor = create_user()
        book = Book.objects.create(title='Title', author='Author', total_copies=1, available_copies=1)
        Loan.objects.create(book=book, member=visitor, returned_at=timezone.now())
        self.client.force_authenticate(self.staff)
        res = self.client.delete(f'/api/users/{visitor.pk}/')
        self.assertEqual(res.status_code, 204)

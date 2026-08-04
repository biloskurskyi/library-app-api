from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from users.models import UserType


class UserManagerTests(TestCase):
    def test_create_user(self):
        user = get_user_model().objects.create_user(
            email='Visitor@EXAMPLE.com',
            password='Password1',
            name='Visitor',
            user_type=UserType.VISITOR,
        )
        self.assertEqual(user.email, 'visitor@example.com')
        self.assertFalse(user.is_active)
        self.assertTrue(user.check_password('Password1'))

    def test_case_variant_email_rejected_by_constraint(self):
        get_user_model().objects.create(email='visitor@example.com', name='Visitor', user_type=UserType.VISITOR)
        with self.assertRaises(IntegrityError):
            get_user_model().objects.create(email='Visitor@example.com', name='Other', user_type=UserType.VISITOR)

    def test_create_user_without_email(self):
        with self.assertRaisesMessage(ValueError, 'The Email field must be set'):
            get_user_model().objects.create_user(
                email='',
                password='Password1',
                name='Visitor',
                user_type=UserType.VISITOR,
            )

    def test_create_superuser(self):
        user = get_user_model().objects.create_superuser(email='admin@example.com', password='Password1')
        self.assertEqual(user.user_type, UserType.LIBRARY)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)

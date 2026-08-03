from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from books.models import Book
from borrowing.models import Loan
from users.models import UserType


class LoanTests(TestCase):
    def setUp(self):
        self.book = Book.objects.create(title='Dune', author='Frank Herbert', total_copies=3, available_copies=3)
        self.member = get_user_model().objects.create_user(
            email='visitor@example.com',
            password='Password1',
            name='Visitor',
            user_type=UserType.VISITOR,
        )

    def test_due_date_defaults_to_30_days(self):
        loan = Loan.objects.create(book=self.book, member=self.member)
        self.assertAlmostEqual(loan.due_date, timezone.now() + timedelta(days=30), delta=timedelta(minutes=1))

    def test_second_active_loan_rejected(self):
        Loan.objects.create(book=self.book, member=self.member)
        with self.assertRaises(IntegrityError):
            Loan.objects.create(book=self.book, member=self.member)

    def test_new_loan_allowed_after_return(self):
        Loan.objects.create(book=self.book, member=self.member, returned_at=timezone.now())
        loan = Loan.objects.create(book=self.book, member=self.member)
        self.assertIsNone(loan.returned_at)

from unittest import mock

from django.test import TestCase

from books.tests.test_api import create_book
from borrowing import services
from borrowing.events import BookBorrowed, BookReturned
from borrowing.models import Loan
from borrowing.notifiers import CeleryEmailNotifier
from common.exceptions import BookUnavailable, LoanAlreadyExists, LoanAlreadyReturned
from users.tests.test_api import create_user


class FakeNotifier:
    def __init__(self):
        self.events = []

    def publish(self, event):
        self.events.append(event)


class BorrowReturnEventsTests(TestCase):
    def setUp(self):
        self.member = create_user()
        self.book = create_book()
        self.notifier = FakeNotifier()

    def test_borrow_publishes_book_borrowed(self):
        services.borrow(self.member, self.book.pk, notifier=self.notifier)
        self.assertEqual(self.notifier.events, [BookBorrowed('Dune', 'Visitor', 'visitor@example.com')])

    def test_return_publishes_book_returned(self):
        loan = services.borrow(self.member, self.book.pk, notifier=self.notifier)
        services.return_loan(self.member, loan.pk, notifier=self.notifier)
        self.assertEqual(self.notifier.events[-1], BookReturned('Dune', 'Visitor', 'visitor@example.com'))
        self.assertEqual(len(self.notifier.events), 2)

    def test_failed_borrow_publishes_nothing(self):
        Loan.objects.create(book=self.book, member=self.member)
        with self.assertRaises(LoanAlreadyExists):
            services.borrow(self.member, self.book.pk, notifier=self.notifier)
        empty = create_book(title='Empty', total_copies=0, available_copies=0)
        with self.assertRaises(BookUnavailable):
            services.borrow(self.member, empty.pk, notifier=self.notifier)
        self.assertEqual(self.notifier.events, [])

    def test_return_twice_raises_domain_error(self):
        loan = services.borrow(self.member, self.book.pk, notifier=self.notifier)
        services.return_loan(self.member, loan.pk, notifier=self.notifier)
        with self.assertRaises(LoanAlreadyReturned):
            services.return_loan(self.member, loan.pk, notifier=self.notifier)

    def test_celery_notifier_defers_until_commit(self):
        with mock.patch('borrowing.notifiers.send_notification_email.delay') as delay:
            with self.captureOnCommitCallbacks(execute=False) as callbacks:
                CeleryEmailNotifier().publish(BookBorrowed('Dune', 'Visitor', 'visitor@example.com'))
            delay.assert_not_called()
            for callback in callbacks:
                callback()
            self.assertEqual(delay.call_count, 2)

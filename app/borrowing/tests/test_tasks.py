from datetime import timedelta
from smtplib import SMTPException
from unittest import mock

from django.core import mail
from django.test import TestCase
from django.utils import timezone

from books.tests.test_api import create_book
from borrowing.models import Loan
from borrowing.tasks import send_overdue_notifications
from users.tests.test_api import create_user


def create_loan(book, member, due_delta):
    loan = Loan.objects.create(book=book, member=member)
    Loan.objects.filter(pk=loan.pk).update(due_date=timezone.now() + due_delta)
    return loan


class OverdueNotificationsTaskTests(TestCase):
    def setUp(self):
        self.member = create_user()
        self.book = create_book()

    def test_sends_email_per_overdue_loan(self):
        create_loan(self.book, self.member, timedelta(days=-1))
        other = create_user(email='other@example.com', name='Other')
        create_loan(create_book(title='Second'), other, timedelta(days=-5))
        send_overdue_notifications()
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].subject, 'Overdue Book Notification')
        self.assertEqual(mail.outbox[0].to, ['visitor@example.com'])
        self.assertEqual(
            mail.outbox[0].body,
            'Dear visitor@example.com,\n\n'
            "The book 'Dune' you borrowed is overdue. "
            'Please return it as soon as possible.',
        )

    def test_skips_not_due_loans(self):
        create_loan(self.book, self.member, timedelta(days=1))
        send_overdue_notifications()
        self.assertEqual(mail.outbox, [])

    def test_skips_returned_loans(self):
        loan = create_loan(self.book, self.member, timedelta(days=-1))
        Loan.objects.filter(pk=loan.pk).update(returned_at=timezone.now())
        send_overdue_notifications()
        self.assertEqual(mail.outbox, [])

    @mock.patch('borrowing.tasks.send_mail')
    def test_failure_does_not_abort_batch(self, mock_send_mail):
        create_loan(self.book, self.member, timedelta(days=-1))
        create_loan(create_book(title='Second'), self.member, timedelta(days=-2))
        mock_send_mail.side_effect = [SMTPException(), None]
        send_overdue_notifications()
        self.assertEqual(mock_send_mail.call_count, 2)

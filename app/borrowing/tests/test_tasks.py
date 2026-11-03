from datetime import timedelta
from smtplib import SMTPException
from unittest import mock

from celery.exceptions import Retry
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from books.tests.test_api import create_book
from borrowing.models import Loan
from borrowing.tasks import send_overdue_notification, send_overdue_notifications
from users.tests.test_api import create_user


def create_loan(book, member, due_delta):
    loan = Loan.objects.create(book=book, member=member)
    Loan.objects.filter(pk=loan.pk).update(due_date=timezone.now() + due_delta)
    return loan


class OverdueNotificationsTaskTests(TestCase):
    def setUp(self):
        self.member = create_user()
        self.book = create_book()

    @mock.patch('borrowing.tasks.send_overdue_notification.delay')
    def test_enqueues_one_task_per_overdue_loan(self, mock_delay):
        first = create_loan(self.book, self.member, timedelta(days=-1))
        other = create_user(email='other@example.com', name='Other')
        second = create_loan(create_book(title='Second'), other, timedelta(days=-5))
        send_overdue_notifications()
        self.assertCountEqual([c.args for c in mock_delay.call_args_list], [(first.pk,), (second.pk,)])

    @mock.patch('borrowing.tasks.send_overdue_notification.delay')
    def test_skips_not_due_and_returned_loans(self, mock_delay):
        create_loan(self.book, self.member, timedelta(days=1))
        returned = create_loan(create_book(title='Second'), self.member, timedelta(days=-1))
        Loan.objects.filter(pk=returned.pk).update(returned_at=timezone.now())
        send_overdue_notifications()
        mock_delay.assert_not_called()

    def test_single_task_sends_email(self):
        loan = create_loan(self.book, self.member, timedelta(days=-1))
        send_overdue_notification(loan.pk)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Overdue Book Notification')
        self.assertEqual(mail.outbox[0].to, ['visitor@example.com'])
        self.assertEqual(
            mail.outbox[0].body,
            'Dear visitor@example.com,\n\n'
            "The book 'Dune' you borrowed is overdue. "
            'Please return it as soon as possible.',
        )

    def test_single_task_skips_returned_loan(self):
        loan = create_loan(self.book, self.member, timedelta(days=-1))
        Loan.objects.filter(pk=loan.pk).update(returned_at=timezone.now())
        send_overdue_notification(loan.pk)
        self.assertEqual(mail.outbox, [])

    def test_retry_policy(self):
        self.assertEqual(send_overdue_notification.max_retries, 3)
        self.assertTrue(send_overdue_notification.retry_backoff)
        self.assertEqual(send_overdue_notification.autoretry_for, (SMTPException, ConnectionError))

    @mock.patch('borrowing.tasks.send_mail', side_effect=SMTPException())
    def test_smtp_failure_is_retried_not_swallowed(self, mock_send_mail):
        loan = create_loan(self.book, self.member, timedelta(days=-1))
        with mock.patch.object(send_overdue_notification, 'retry', side_effect=Retry()) as mock_retry:
            with self.assertRaises(Retry):
                send_overdue_notification(loan.pk)
        mock_retry.assert_called_once()

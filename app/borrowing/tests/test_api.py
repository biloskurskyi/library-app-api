from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from books.tests.test_api import create_book
from borrowing.models import Loan
from borrowing.tasks import send_notification_email
from users.models import UserType
from users.tests.test_api import create_user


class BorrowApiTests(APITestCase):
    def setUp(self):
        self.visitor = create_user()
        self.book = create_book()
        self.client.force_authenticate(self.visitor)

    @mock.patch('borrowing.services.send_notification_email.delay')
    def test_borrow(self, mock_delay):
        res = self.client.post('/api/loans/', {'book': self.book.pk})
        self.assertEqual(res.status_code, 201)
        loan = Loan.objects.get(pk=res.data['id'])
        self.assertEqual(res.data, {
            'id': loan.id,
            'book': self.book.pk,
            'member': self.visitor.pk,
            'borrowed_at': loan.borrowed_at.isoformat().replace('+00:00', 'Z'),
            'due_date': loan.due_date.isoformat().replace('+00:00', 'Z'),
            'returned_at': None,
        })
        self.assertAlmostEqual(loan.due_date, timezone.now() + timedelta(days=30), delta=timedelta(minutes=1))
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 4)

    @mock.patch('borrowing.services.send_notification_email.delay')
    def test_borrow_queues_borrower_and_active_staff_emails(self, mock_delay):
        create_user(email='staff@example.com', user_type=UserType.LIBRARY, name='Staff')
        create_user(email='inactive@example.com', user_type=UserType.LIBRARY, name='Gone', is_active=False)
        self.client.post('/api/loans/', {'book': self.book.pk})
        borrower_call, staff_call = mock_delay.call_args_list
        self.assertEqual(borrower_call.args, (
            'Book Borrowed',
            'You have successfully borrowed the book: Dune.',
            ['visitor@example.com'],
        ))
        self.assertEqual(staff_call.args, (
            'Book Borrowed Notification',
            "The book 'Dune' was borrowed by Visitor (Email: visitor@example.com).",
            ['staff@example.com'],
        ))

    @mock.patch('borrowing.services.send_notification_email.delay')
    def test_borrow_no_copies_fails(self, mock_delay):
        book = create_book(title='Empty', total_copies=0, available_copies=0)
        res = self.client.post('/api/loans/', {'book': book.pk})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['detail'], ['No copies of this book are available.'])
        mock_delay.assert_not_called()

    @mock.patch('borrowing.services.send_notification_email.delay')
    def test_double_borrow_fails(self, mock_delay):
        Loan.objects.create(book=self.book, member=self.visitor)
        res = self.client.post('/api/loans/', {'book': self.book.pk})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['detail'], ['You have already borrowed this book.'])
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 5)

    @mock.patch('borrowing.services.send_notification_email.delay')
    def test_borrow_again_after_return(self, mock_delay):
        Loan.objects.create(book=self.book, member=self.visitor, returned_at=timezone.now())
        res = self.client.post('/api/loans/', {'book': self.book.pk})
        self.assertEqual(res.status_code, 201)

    def test_borrow_missing_book_fails(self):
        res = self.client.post('/api/loans/', {'book': 999})
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data['code'], 'NOT_FOUND')

    def test_borrow_without_body_fails(self):
        res = self.client.post('/api/loans/', {})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['code'], 'VALIDATION_ERROR')

    def test_borrow_by_staff_fails(self):
        self.client.force_authenticate(create_user(email='staff@example.com', user_type=UserType.LIBRARY))
        res = self.client.post('/api/loans/', {'book': self.book.pk})
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data['code'], 'PERMISSION_DENIED')

    def test_borrow_requires_authentication(self):
        self.client.force_authenticate(None)
        res = self.client.post('/api/loans/', {'book': self.book.pk})
        self.assertEqual(res.status_code, 401)


class ReturnLoanApiTests(APITestCase):
    def setUp(self):
        self.visitor = create_user()
        self.book = create_book(total_copies=5, available_copies=4)
        self.loan = Loan.objects.create(book=self.book, member=self.visitor)
        self.client.force_authenticate(self.visitor)

    @mock.patch('borrowing.services.send_notification_email.delay')
    def test_return(self, mock_delay):
        res = self.client.post(f'/api/loans/{self.loan.pk}/returned/')
        self.assertEqual(res.status_code, 201)
        self.loan.refresh_from_db()
        self.assertIsNotNone(self.loan.returned_at)
        self.assertEqual(res.data['id'], self.loan.pk)
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 5)
        borrower_call, staff_call = mock_delay.call_args_list
        self.assertEqual(borrower_call.args, (
            'Book Returned',
            'You have successfully returned the book: Dune.',
            ['visitor@example.com'],
        ))
        self.assertEqual(staff_call.args[0], 'Book Returned Notification')
        self.assertEqual(staff_call.args[1], "The book 'Dune' was returned by Visitor (Email: visitor@example.com).")

    @mock.patch('borrowing.services.send_notification_email.delay')
    def test_return_increment_capped_at_total_copies(self, mock_delay):
        book = create_book(title='Shrunk', total_copies=1, available_copies=1)
        loan = Loan.objects.create(book=book, member=self.visitor)
        res = self.client.post(f'/api/loans/{loan.pk}/returned/')
        self.assertEqual(res.status_code, 201)
        book.refresh_from_db()
        self.assertEqual(book.available_copies, 1)

    @mock.patch('borrowing.services.send_notification_email.delay')
    def test_return_twice_fails(self, mock_delay):
        self.client.post(f'/api/loans/{self.loan.pk}/returned/')
        res = self.client.post(f'/api/loans/{self.loan.pk}/returned/')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data['detail'], 'No record found for this book or you have already returned it.')
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 5)

    def test_return_missing_loan_fails(self):
        res = self.client.post('/api/loans/999/returned/')
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data['detail'], 'No record found for this book or you have already returned it.')

    def test_return_other_members_loan_fails(self):
        other = create_user(email='other@example.com', name='Other')
        self.client.force_authenticate(other)
        res = self.client.post(f'/api/loans/{self.loan.pk}/returned/')
        self.assertEqual(res.status_code, 404)

    def test_return_by_staff_fails(self):
        self.client.force_authenticate(create_user(email='staff@example.com', user_type=UserType.LIBRARY))
        res = self.client.post(f'/api/loans/{self.loan.pk}/returned/')
        self.assertEqual(res.status_code, 403)

    def test_return_requires_authentication(self):
        self.client.force_authenticate(None)
        res = self.client.post(f'/api/loans/{self.loan.pk}/returned/')
        self.assertEqual(res.status_code, 401)


class LoanListApiTests(APITestCase):
    def setUp(self):
        self.staff = create_user(email='staff@example.com', user_type=UserType.LIBRARY, name='Staff')
        self.visitor = create_user()
        self.book = create_book(total_copies=5, available_copies=3)

    def test_visitor_sees_own_active_loans(self):
        loan = Loan.objects.create(book=self.book, member=self.visitor)
        Loan.objects.create(
            book=create_book(title='Returned'), member=self.visitor, returned_at=timezone.now(),
        )
        Loan.objects.create(book=create_book(title='Other'), member=create_user(email='other@example.com'))
        self.client.force_authenticate(self.visitor)
        res = self.client.get('/api/loans/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual([item['id'] for item in res.data], [loan.pk])

    def test_visitor_empty_list(self):
        self.client.force_authenticate(self.visitor)
        res = self.client.get('/api/loans/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, [])

    def test_visitor_list_ordered_by_borrowed_at(self):
        first = Loan.objects.create(book=self.book, member=self.visitor)
        second = Loan.objects.create(book=create_book(title='Second'), member=self.visitor)
        self.client.force_authenticate(self.visitor)
        res = self.client.get('/api/loans/')
        self.assertEqual([item['id'] for item in res.data], [first.pk, second.pk])

    def test_staff_sees_member_loans(self):
        loan = Loan.objects.create(book=self.book, member=self.visitor)
        self.client.force_authenticate(self.staff)
        res = self.client.get(f'/api/loans/?member={self.visitor.pk}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual([item['id'] for item in res.data], [loan.pk])

    def test_staff_member_empty_list(self):
        self.client.force_authenticate(self.staff)
        res = self.client.get(f'/api/loans/?member={self.visitor.pk}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, [])

    def test_staff_without_member_fails(self):
        self.client.force_authenticate(self.staff)
        res = self.client.get('/api/loans/')
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data['code'], 'VALIDATION_ERROR')

    def test_staff_member_not_integer_fails(self):
        self.client.force_authenticate(self.staff)
        res = self.client.get('/api/loans/?member=abc')
        self.assertEqual(res.status_code, 400)

    def test_staff_missing_member_fails(self):
        self.client.force_authenticate(self.staff)
        res = self.client.get('/api/loans/?member=999')
        self.assertEqual(res.status_code, 404)

    def test_staff_target_staff_fails(self):
        other = create_user(email='other@example.com', user_type=UserType.LIBRARY, name='Other')
        self.client.force_authenticate(self.staff)
        res = self.client.get(f'/api/loans/?member={other.pk}')
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data['detail'], 'This user is a library staff member.')

    def test_list_requires_authentication(self):
        res = self.client.get('/api/loans/')
        self.assertEqual(res.status_code, 401)


class NotificationTaskTests(TestCase):
    def test_send_notification_email(self):
        send_notification_email('Subject', 'Message', ['to@example.com'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Subject')
        self.assertEqual(mail.outbox[0].body, 'Message')
        self.assertEqual(mail.outbox[0].to, ['to@example.com'])

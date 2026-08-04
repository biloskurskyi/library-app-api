from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import (NotFound, PermissionDenied,
                                       ValidationError)

from books.models import Book
from users.models import User, UserType

from .models import Loan
from .tasks import send_notification_email


def borrow(actor, book_id):
    with transaction.atomic():
        book = get_object_or_404(Book.objects.select_for_update(), pk=book_id)
        if book.available_copies <= 0:
            raise ValidationError('No copies of this book are available.')
        if Loan.objects.filter(book=book, member=actor, returned_at__isnull=True).exists():
            raise ValidationError('You have already borrowed this book.')
        try:
            loan = Loan.objects.create(book=book, member=actor)
        except IntegrityError:
            raise ValidationError('You have already borrowed this book.')
        book.available_copies -= 1
        book.save(update_fields=['available_copies'])
    _queue_emails(book, actor, 'Borrowed')
    return loan


def return_loan(actor, loan_id):
    with transaction.atomic():
        loan = Loan.objects.select_for_update().filter(
            pk=loan_id, member=actor, returned_at__isnull=True,
        ).first()
        if loan is None:
            raise NotFound('No record found for this book or you have already returned it.')
        book = Book.objects.select_for_update().get(pk=loan.book_id)
        loan.returned_at = timezone.now()
        loan.save(update_fields=['returned_at'])
        if book.available_copies < book.total_copies:
            book.available_copies += 1
            book.save(update_fields=['available_copies'])
    _queue_emails(book, actor, 'Returned')
    return loan


def active_loans(actor, member_id=None):
    if actor.user_type == UserType.VISITOR:
        return _active_loans_of(actor)
    if member_id is None:
        raise ValidationError('The member query parameter is required.')
    member = get_object_or_404(User, pk=member_id)
    if member.user_type == UserType.LIBRARY:
        raise PermissionDenied('This user is a library staff member.')
    return _active_loans_of(member)


def _active_loans_of(member):
    return member.loans.filter(returned_at__isnull=True)


def _queue_emails(book, member, action):
    send_notification_email.delay(
        f'Book {action}',
        f'You have successfully {action.lower()} the book: {book.title}.',
        [member.email],
    )
    send_notification_email.delay(
        f'Book {action} Notification',
        f"The book '{book.title}' was {action.lower()} by {member.name} (Email: {member.email}).",
        _staff_emails(),
    )


def _staff_emails():
    return list(User.objects.filter(user_type=UserType.LIBRARY, is_active=True).values_list('email', flat=True))

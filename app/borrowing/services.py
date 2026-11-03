from django.db import IntegrityError, transaction
from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.utils import timezone

from books.models import Book
from common.exceptions import (
    BookUnavailable,
    LoanAlreadyExists,
    LoanAlreadyReturned,
    MemberRequired,
    StaffMemberNotAllowed,
)
from common.notifier import Notifier
from users.models import User, UserType

from .events import BookBorrowed, BookReturned
from .models import Loan
from .notifiers import CeleryEmailNotifier


def borrow(actor: User, book_id: int, notifier: Notifier | None = None) -> Loan:
    notifier = notifier or CeleryEmailNotifier()
    with transaction.atomic():
        book = get_object_or_404(Book.objects.select_for_update(), pk=book_id)
        if book.available_copies <= 0:
            raise BookUnavailable()
        if Loan.objects.filter(book=book, member=actor, returned_at__isnull=True).exists():
            raise LoanAlreadyExists()
        try:
            loan = Loan.objects.create(book=book, member=actor)
        except IntegrityError:
            raise LoanAlreadyExists() from None
        book.available_copies -= 1
        book.save(update_fields=['available_copies'])
        notifier.publish(BookBorrowed(book.title, actor.name, actor.email))
    return loan


def return_loan(actor: User, loan_id: int, notifier: Notifier | None = None) -> Loan:
    notifier = notifier or CeleryEmailNotifier()
    with transaction.atomic():
        loan = Loan.objects.select_for_update().filter(
            pk=loan_id, member=actor, returned_at__isnull=True,
        ).first()
        if loan is None:
            raise LoanAlreadyReturned()
        book = Book.objects.select_for_update().get(pk=loan.book_id)
        loan.returned_at = timezone.now()
        loan.save(update_fields=['returned_at'])
        if book.available_copies < book.total_copies:
            book.available_copies += 1
            book.save(update_fields=['available_copies'])
        notifier.publish(BookReturned(book.title, actor.name, actor.email))
    return loan


def active_loans(actor: User, member_id: int | None = None) -> QuerySet[Loan]:
    if actor.user_type == UserType.VISITOR:
        return _active_loans_of(actor)
    if member_id is None:
        raise MemberRequired()
    member = get_object_or_404(User, pk=member_id)
    if member.user_type == UserType.LIBRARY:
        raise StaffMemberNotAllowed()
    return _active_loans_of(member)


def _active_loans_of(member: User) -> QuerySet[Loan]:
    return member.loans.filter(returned_at__isnull=True)

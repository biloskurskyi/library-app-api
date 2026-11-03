from django.db import transaction

from users.models import User, UserType

from .events import BookBorrowed, BookReturned
from .tasks import send_notification_email

_ACTIONS = {BookBorrowed: 'Borrowed', BookReturned: 'Returned'}


class CeleryEmailNotifier:
    """Sends borrower and staff emails through Celery once the surrounding transaction commits."""

    def publish(self, event: BookBorrowed | BookReturned) -> None:
        transaction.on_commit(lambda: self._send(event))

    def _send(self, event: BookBorrowed | BookReturned) -> None:
        action = _ACTIONS[type(event)]
        send_notification_email.delay(
            f'Book {action}',
            f'You have successfully {action.lower()} the book: {event.book_title}.',
            [event.member_email],
        )
        send_notification_email.delay(
            f'Book {action} Notification',
            f"The book '{event.book_title}' was {action.lower()} by {event.member_name} (Email: {event.member_email}).",
            _staff_emails(),
        )


def _staff_emails() -> list[str]:
    return list(User.objects.filter(user_type=UserType.LIBRARY, is_active=True).values_list('email', flat=True))

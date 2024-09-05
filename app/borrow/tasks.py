from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from core.models import BorrowRecord


@shared_task
def send_notification_email(subject, message, recipient_list):
    """
    Send a notification email to the specified recipients.
    """
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        recipient_list
    )


@shared_task
def send_overdue_notifications():
    """
    Send overdue notifications for books that are past their due date.
    """
    overdue_records = BorrowRecord.objects.filter(due_date__lt=timezone.now(), returned_at__isnull=True)

    for record in overdue_records:
        send_mail(
            subject="Overdue Book Notification",
            message=f"Dear {record.member.email},\n\nThe book '{record.book.title}' you borrowed is overdue. "
                    f"Please return it as soon as possible.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[record.member.email],
        )
        print(f"Book {record.book.title} is overdue for {record.member.email}")

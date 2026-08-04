import logging
from smtplib import SMTPException

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Loan

logger = logging.getLogger(__name__)


@shared_task(autoretry_for=(SMTPException,), retry_backoff=True, max_retries=3)
def send_notification_email(subject, message, recipient_list):
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    logger.info('Notification email "%s" sent to %s', subject, recipient_list)


@shared_task
def send_overdue_notifications():
    loans = Loan.objects.filter(
        due_date__lt=timezone.now(), returned_at__isnull=True,
    ).select_related('member', 'book')
    for loan in loans:
        try:
            send_mail(
                'Overdue Book Notification',
                f'Dear {loan.member.email},\n\n'
                f"The book '{loan.book.title}' you borrowed is overdue. "
                'Please return it as soon as possible.',
                settings.DEFAULT_FROM_EMAIL,
                [loan.member.email],
            )
            logger.info('Overdue notification sent to %s for "%s"', loan.member.email, loan.book.title)
        except Exception:
            logger.exception('Overdue notification to %s failed', loan.member.email)

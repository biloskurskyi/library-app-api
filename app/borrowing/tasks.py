import logging
from smtplib import SMTPException

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(autoretry_for=(SMTPException,), retry_backoff=True, max_retries=3)
def send_notification_email(subject, message, recipient_list):
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
    logger.info('Notification email "%s" sent to %s', subject, recipient_list)

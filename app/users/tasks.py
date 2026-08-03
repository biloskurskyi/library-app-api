import logging
from smtplib import SMTPException

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


@shared_task(autoretry_for=(SMTPException,), retry_backoff=True, max_retries=3)
def send_activation_email(user_email, user_name, token):
    send_mail(
        'Activate your account',
        f'Hello {user_name},\n\n'
        f'Please activate your account using the following link: '
        f'{settings.APP_BASE_URL}/api/activate/{token}/',
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
    )
    logger.info('Activation email sent to %s', user_email)

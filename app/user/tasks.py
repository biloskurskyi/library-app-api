from django.conf import settings
from django.core.mail import send_mail

from celery_folder.celery_app import app


@app.task
def send_activation_email(user_email, user_name, user_id):
    """
        Sends an account activation email to the user with a link to activate their account.

        Args:
            user_email (str): The email address of the user.
            user_name (str): The name of the user.
            user_id (int): The ID of the user for the activation link.

        Returns:
            str: A message indicating whether the email was sent successfully or an error occurred.
    """
    subject = 'Activate your account'
    message = (f'Hello {user_name},\n\nPlease activate your account using the following link:'
               f' http://localhost:8321/api/activate/{user_id}/')
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [user_email]

    try:
        send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        return 'Email sent successfully'
    except Exception as e:
        return f'Error sending email: {e}'

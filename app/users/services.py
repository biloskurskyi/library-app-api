from datetime import timedelta

from django.core import signing
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied, ValidationError

from .models import User, UserType
from .tasks import send_activation_email

ACTIVATION_MAX_AGE = timedelta(days=3)


def register(data):
    user = User.objects.create_user(user_type=UserType.VISITOR, **data)
    send_activation_email.delay(user.email, user.name, activation_token(user))
    return user


def activation_token(user):
    return signing.TimestampSigner().sign(str(user.pk))


def activate(token):
    try:
        user_id = signing.TimestampSigner().unsign(token, max_age=ACTIVATION_MAX_AGE)
    except signing.BadSignature:
        raise ValidationError('Invalid or expired activation link.')
    user = get_object_or_404(User, pk=user_id)
    if user.is_active:
        return 'User is active.'
    user.is_active = True
    user.save(update_fields=['is_active'])
    return 'User activated successfully.'


def destroy(actor, user_id):
    with transaction.atomic():
        user = get_object_or_404(User.objects.select_for_update(), pk=user_id)
        if user.user_type == UserType.LIBRARY and user != actor:
            raise PermissionDenied('Cannot delete a library user.')
        if user.loans.filter(returned_at__isnull=True).exists():
            raise PermissionDenied('Cannot delete user with existing borrow records.')
        user.delete()

from enum import Enum

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.views import exception_handler


class DomainError(Exception):
    """Base class for business-rule violations raised by the service layer."""

    default_message = 'A domain rule was violated.'
    api_exception: type[exceptions.APIException] = exceptions.ValidationError

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class BookUnavailable(DomainError):
    default_message = 'No copies of this book are available.'


class LoanAlreadyExists(DomainError):
    default_message = 'You have already borrowed this book.'


class LoanAlreadyReturned(DomainError):
    default_message = 'No record found for this book or you have already returned it.'
    api_exception = exceptions.NotFound


class MemberRequired(DomainError):
    default_message = 'The member query parameter is required.'


class StaffMemberNotAllowed(DomainError):
    default_message = 'This user is a library staff member.'
    api_exception = exceptions.PermissionDenied


class ErrorCode(Enum):
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    NOT_AUTHENTICATED = 'NOT_AUTHENTICATED'
    AUTHENTICATION_FAILED = 'AUTHENTICATION_FAILED'
    PERMISSION_DENIED = 'PERMISSION_DENIED'
    NOT_FOUND = 'NOT_FOUND'
    METHOD_NOT_ALLOWED = 'METHOD_NOT_ALLOWED'
    THROTTLED = 'THROTTLED'
    ERROR = 'ERROR'


_EXCEPTION_CODES = (
    (exceptions.ValidationError, ErrorCode.VALIDATION_ERROR),
    (exceptions.NotAuthenticated, ErrorCode.NOT_AUTHENTICATED),
    (exceptions.AuthenticationFailed, ErrorCode.AUTHENTICATION_FAILED),
    (exceptions.PermissionDenied, ErrorCode.PERMISSION_DENIED),
    (exceptions.NotFound, ErrorCode.NOT_FOUND),
    (exceptions.MethodNotAllowed, ErrorCode.METHOD_NOT_ALLOWED),
    (exceptions.Throttled, ErrorCode.THROTTLED),
    (Http404, ErrorCode.NOT_FOUND),
    (PermissionDenied, ErrorCode.PERMISSION_DENIED),
)


def drf_exception_handler(exc, context):
    if isinstance(exc, DomainError):
        exc = exc.api_exception(exc.message)
    response = exception_handler(exc, context)
    if response is None:
        return None
    response.data = {'code': _error_code(exc).value, 'detail': _detail(response.data)}
    return response


def _error_code(exc):
    for exception_class, code in _EXCEPTION_CODES:
        if isinstance(exc, exception_class):
            return code
    return ErrorCode.ERROR


def _detail(data):
    if isinstance(data, dict) and set(data) == {'detail'}:
        return data['detail']
    return data

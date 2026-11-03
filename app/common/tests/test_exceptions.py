from django.test import SimpleTestCase

from common.exceptions import (
    BookUnavailable,
    DomainError,
    LoanAlreadyExists,
    LoanAlreadyReturned,
    MemberRequired,
    StaffMemberNotAllowed,
    drf_exception_handler,
)


class DomainErrorHandlerTests(SimpleTestCase):
    def assert_maps_to(self, exc, status_code, code):
        response = drf_exception_handler(exc, {})
        self.assertEqual(response.status_code, status_code)
        self.assertEqual(response.data['code'], code)

    def test_status_and_code_per_domain_error(self):
        self.assert_maps_to(BookUnavailable(), 400, 'VALIDATION_ERROR')
        self.assert_maps_to(LoanAlreadyExists(), 400, 'VALIDATION_ERROR')
        self.assert_maps_to(MemberRequired(), 400, 'VALIDATION_ERROR')
        self.assert_maps_to(LoanAlreadyReturned(), 404, 'NOT_FOUND')
        self.assert_maps_to(StaffMemberNotAllowed(), 403, 'PERMISSION_DENIED')

    def test_custom_message_is_kept(self):
        response = drf_exception_handler(LoanAlreadyReturned('gone'), {})
        self.assertEqual(response.data['detail'], 'gone')

    def test_domain_errors_share_base(self):
        self.assertTrue(issubclass(BookUnavailable, DomainError))

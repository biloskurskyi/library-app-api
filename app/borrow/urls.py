from django.urls import path

from .views import (BorrowBookView, MyBorrowedBooksView, ReturnBookView,
                    UserBorrowedBooksView)

app_name = 'borrow'

"""
URL patterns for borrow-related operations.
"""

urlpatterns = [
    path('borrow/<int:pk>/', BorrowBookView.as_view(), name='borrow-book'),
    path('return/<int:pk>/', ReturnBookView.as_view(), name='return-book'),
    path('user-borrowed-books/<int:user_id>/', UserBorrowedBooksView.as_view(), name='user-borrowed-books'),
    path('my-borrowed-books/', MyBorrowedBooksView.as_view(), name='my-borrowed-books'),
]

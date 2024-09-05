from django.urls import path

from .views import BookDetailView, BooksView

app_name = 'books'

"""
URL patterns for books-related operations.
"""

urlpatterns = [
    path('books/', BooksView.as_view(), name='books-info'),
    path('book/<int:pk>/', BookDetailView.as_view(), name='book-detail'),
]

from django.urls import path

from .views import BookDetailView, BooksView

app_name = 'books'

urlpatterns = [
    path('books/', BooksView.as_view(), name='books'),
    path('book/<int:pk>/', BookDetailView.as_view(), name='book-detail'),
]

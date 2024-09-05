from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Book

from .serializers import BookSerializer


class BooksView(APIView):
    """
    View to list all books or create a new book.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        """
        Create a new book.
        Only accessible by users with LIBRARY_USER type.
        """
        user = request.user
        if user.user_type != user.LIBRARY_USER:
            return Response({'detail': 'You do not have permission to add books.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """
        List all books.
        """
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BookDetailView(APIView):
    """
    View to retrieve, update, or delete a specific book.
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, pk):
        """
        Retrieve a specific book by ID.
        """
        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({"message": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = BookSerializer(book)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk):
        """
        Update a specific book by ID.
        Only accessible by users with LIBRARY_USER type.
        """
        user = request.user
        if user.user_type != user.LIBRARY_USER:
            return Response({'detail': 'You do not have permission to update books.'},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({"message": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        data = request.data
        total_copies = data.get('total_copies')

        if total_copies is not None:
            if total_copies < book.available_copies:
                book.total_copies = book.available_copies
            elif total_copies > book.total_copies:
                book.available_copies += (total_copies - book.total_copies)
                book.total_copies = total_copies
            else:
                book.total_copies = total_copies
        else:
            serializer = BookSerializer(book, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        book.save()
        return Response(BookSerializer(book).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        """
        Delete a specific book by ID.
        Only accessible by users with LIBRARY_USER type.
        """
        user = request.user
        if user.user_type != user.LIBRARY_USER:
            return Response({'detail': 'You do not have permission to delete books.'},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            book = Book.objects.get(pk=pk)
        except Book.DoesNotExist:
            return Response({"message": "Book not found"}, status=status.HTTP_404_NOT_FOUND)

        if book.available_copies != book.total_copies:
            return Response({'detail': 'Cannot delete the book because some copies are currently borrowed.'},
                            status=status.HTTP_400_BAD_REQUEST)

        book.delete()
        return Response({"message": "Book deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Book, BorrowRecord, User

from .serializers import BorrowRecordSerializer
from .tasks import send_notification_email


class BorrowBookView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        if request.user.user_type != request.user.VISITOR_USER:
            return Response({'detail': 'You do not have permission to borrow books.'},
                            status=status.HTTP_403_FORBIDDEN)

        book = get_object_or_404(Book, pk=pk)

        if book.available_copies <= 0:
            return Response({'detail': 'No copies of this book are available.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if BorrowRecord.objects.filter(book=book, member=request.user, returned_at__isnull=True).exists():
            return Response({'detail': 'You have already borrowed this book.'},
                            status=status.HTTP_400_BAD_REQUEST)

        borrow_record = BorrowRecord(book=book, member=request.user)
        borrow_record.save()

        book.available_copies -= 1
        book.save()

        send_notification_email.delay(
            subject='Book Borrowed',
            message=f'You have successfully borrowed the book: {book.title}.',
            recipient_list=[request.user.email]
        )

        User = get_user_model()
        library_users = User.objects.filter(user_type=User.LIBRARY_USER)

        library_emails = [user.email for user in library_users]
        send_notification_email.delay(
            subject="Book Borrowed Notification",
            message=f"The book '{book.title}' was borrowed by {request.user.name} (Email: {request.user.email}).",
            recipient_list=library_emails
        )

        serializer = BorrowRecordSerializer(borrow_record)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ReturnBookView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        if request.user.user_type != request.user.VISITOR_USER:
            return Response({'detail': 'You do not have permission to return books.'},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            borrow_record = BorrowRecord.objects.get(book_id=pk, member=request.user, returned_at__isnull=True)
        except BorrowRecord.DoesNotExist:
            return Response({'detail': 'No record found for this book or you have already returned it.'},
                            status=status.HTTP_404_NOT_FOUND)

        borrow_record.returned_at = timezone.now()
        borrow_record.save()

        book = borrow_record.book
        book.available_copies += 1
        book.save()

        send_notification_email.delay(
            subject="Book Returned",
            message=f"You have successfully returned the book: {book.title}.",
            recipient_list=[request.user.email]
        )

        User = get_user_model()
        library_users = User.objects.filter(user_type=User.LIBRARY_USER)

        library_emails = [user.email for user in library_users]
        send_notification_email.delay(
            subject="Book Returned Notification",
            message=f"The book '{book.title}' was returned by {request.user.name} (Email: {request.user.email}).",
            recipient_list=library_emails
        )

        serializer = BorrowRecordSerializer(borrow_record)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserBorrowedBooksView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_id):
        if request.user.user_type != request.user.LIBRARY_USER:
            return Response({'detail': 'You do not have permission to view borrowed books.'},
                            status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'},
                            status=status.HTTP_404_NOT_FOUND)

        if user.user_type == User.LIBRARY_USER:
            return Response({'detail': 'This user is a library staff member.'},
                            status=status.HTTP_403_FORBIDDEN)

        borrowed_books = BorrowRecord.objects.filter(member_id=user_id, returned_at__isnull=True)

        if not borrowed_books.exists():
            return Response({'detail': 'No borrowed books found for this user.'},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = BorrowRecordSerializer(borrowed_books, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MyBorrowedBooksView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if request.user.user_type == request.user.LIBRARY_USER:
            return Response({'detail': 'You do not have permission to view borrowed books.'},
                            status=status.HTTP_403_FORBIDDEN)

        borrowed_books = BorrowRecord.objects.filter(member=request.user, returned_at__isnull=True)

        if not borrowed_books.exists():
            return Response({'detail': 'No borrowed books found for you.'},
                            status=status.HTTP_404_NOT_FOUND)

        serializer = BorrowRecordSerializer(borrowed_books, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

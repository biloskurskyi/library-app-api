from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsLibraryUser

from . import services
from .models import Book
from .serializers import BookSerializer


class BookListView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsLibraryUser()]
        return [IsAuthenticated()]

    def get(self, request):
        return Response(BookSerializer(Book.objects.all(), many=True).data)

    def post(self, request):
        serializer = BookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BookDetailView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsLibraryUser()]

    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        return Response(BookSerializer(book).data)

    def patch(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        serializer = BookSerializer(book, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        book = services.update(pk, serializer.validated_data)
        return Response(BookSerializer(book).data)

    def delete(self, request, pk):
        services.destroy(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

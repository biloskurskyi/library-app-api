from rest_framework import serializers

from core.models import Book


class BookSerializer(serializers.ModelSerializer):
    """
    Serializer for the Book model. Handles creation and validation of book instances.
    """
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'total_copies', 'available_copies']
        read_only_fields = ['available_copies']

    def create(self, validated_data):
        """
        Sets available copies to the total number of copies when creating a new book.
        """
        validated_data['available_copies'] = validated_data['total_copies']
        return super().create(validated_data)

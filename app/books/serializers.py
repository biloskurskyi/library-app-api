from rest_framework import serializers

from core.models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'total_copies', 'available_copies']
        read_only_fields = ['available_copies']

    def create(self, validated_data):
        validated_data['available_copies'] = validated_data['total_copies']
        return super().create(validated_data)

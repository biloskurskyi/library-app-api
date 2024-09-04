from rest_framework import serializers

from core.models import BorrowRecord


class BorrowRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowRecord
        fields = ['id', 'book', 'member', 'borrowed_at', 'due_date', 'returned_at']

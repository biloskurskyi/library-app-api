from rest_framework import serializers

from .models import Loan


class LoanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ['id', 'book', 'member', 'borrowed_at', 'due_date', 'returned_at']


class CreateLoanSerializer(serializers.Serializer):
    book = serializers.IntegerField()


class LoanFilterSerializer(serializers.Serializer):
    member = serializers.IntegerField(required=False)

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.permissions import IsVisitor

from . import services
from .serializers import (CreateLoanSerializer, LoanFilterSerializer,
                          LoanSerializer)


class LoanListView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsVisitor()]
        return [IsAuthenticated()]

    def get(self, request):
        serializer = LoanFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        loans = services.active_loans(request.user, serializer.validated_data.get('member'))
        return Response(LoanSerializer(loans, many=True).data)

    def post(self, request):
        serializer = CreateLoanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        loan = services.borrow(request.user, serializer.validated_data['book'])
        return Response(LoanSerializer(loan).data, status=status.HTTP_201_CREATED)


class ReturnedLoanView(APIView):
    permission_classes = [IsVisitor]

    def post(self, request, pk):
        loan = services.return_loan(request.user, pk)
        return Response(LoanSerializer(loan).data, status=status.HTTP_201_CREATED)

import datetime

import jwt
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import BorrowRecord, User

from .serializers import UserSerializer
from .tasks import send_activation_email


class RegisterView(APIView):
    """
    Handles user registration. Validates the provided data, creates a new user, and sends an activation email.

    POST request data should include 'email' and 'password'.
    """

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if user.email:
            send_activation_email.delay(user.email, user.name, user.id)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ActivateUserView(APIView):
    """
    Activates a user account. The user must be found by their ID and must not already be active.

    GET request URL should include 'user_id'.
    """

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_active:
            return HttpResponse("User is active.")

        user.is_active = True
        user.save()

        return HttpResponse("User activated successfully.")


class LoginView(APIView):
    """
    Authenticates a user and provides a JWT token upon successful login.

    POST request data should include 'email' and 'password'.
    """

    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()
        if not user or not user.check_password(password) or not user.is_active:
            raise AuthenticationFailed('User not found or password is incorrect')

        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, 'secret', algorithm='HS256')

        return Response({'jwt': token, 'id': user.id, 'user_type': user.user_type})


class LogoutView(APIView):
    """
    Handles user logout by deleting the JWT cookie.

    Requires authentication.
    """
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'success'
        }
        return response


class DeleteUserView(APIView):
    """
    Allows a library user to delete their own account.

    Requires authentication.
    """
    permission_classes = (IsAuthenticated,)

    def delete(self, request):
        user = request.user

        if user.user_type != user.LIBRARY_USER:
            return JsonResponse({'error': 'Only library users can delete themselves.'},
                                status=status.HTTP_403_FORBIDDEN)

        user.delete()

        return Response({'message': 'User deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


class DeleteVisitorUserView(APIView):
    """
    Allows a library user to delete a visitor user account, provided that the visitor does not have any active
    borrow records.

    Requires authentication.
    """
    permission_classes = (IsAuthenticated,)

    def delete(self, request, user_id):
        current_user = request.user

        if current_user.user_type != User.LIBRARY_USER:
            return JsonResponse({'error': 'Only library users can delete other users.'},
                                status=status.HTTP_403_FORBIDDEN)

        user_to_delete = get_object_or_404(User, id=user_id)

        if user_to_delete.user_type == User.LIBRARY_USER:
            return JsonResponse({'error': 'Cannot delete a library user.'}, status=status.HTTP_403_FORBIDDEN)

        has_borrow_records = BorrowRecord.objects.filter(member=user_to_delete, returned_at__isnull=True).exists()
        if has_borrow_records:
            return JsonResponse({'error': 'Cannot delete user with existing borrow records.'},
                                status=status.HTTP_403_FORBIDDEN)

        user_to_delete.delete()

        return Response({'message': 'Visitor user deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

import datetime
from django.core.mail import send_mail
import jwt
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, JsonResponse

from core.models import User

from .serializers import UserSerializer
from .tasks import send_activation_email
from app import settings


# Create your views here.

class RegisterView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        base_url = 'http://localhost:8321/api/activate/'

        if user.email:
            # subject = 'Activate your account'
            # message = f'Hello {user.name},\n\nPlease activate your account using the following link: {base_url}{user.id}/'
            # from_email = settings.EMAIL_HOST_USER
            # recipient_list = [user.email]
            #
            # send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            send_activation_email.delay(user.email, user.name, user.id)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ActivateUserView(APIView):
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
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'success'
        }
        return response

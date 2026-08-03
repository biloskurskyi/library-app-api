from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from common.permissions import IsLibraryUser

from . import services
from .serializers import LoginSerializer, UserSerializer


class UserListView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.register(serializer.validated_data)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = [IsLibraryUser]

    def delete(self, request, pk):
        services.destroy(request.user, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ActivationView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        return Response({'detail': services.activate(token)})


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer

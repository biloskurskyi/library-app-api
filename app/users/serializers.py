from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'user_type']
        read_only_fields = ['user_type']
        extra_kwargs = {'password': {'write_only': True, 'validators': [validate_password]}}


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data.update(id=self.user.id, user_type=self.user.user_type)
        return data

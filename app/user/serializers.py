from rest_framework import serializers

from core.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'user_type']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data, is_active=False)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance

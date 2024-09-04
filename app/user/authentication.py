import jwt
from rest_framework import authentication, exceptions

from core.models import User


class JWTAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        token = auth_header.split(' ')[1]

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise exceptions.AuthenticationFailed('Invalid token')

        user = User.objects.filter(id=payload['id']).first()

        if user is None:
            raise exceptions.AuthenticationFailed('User not found')

        return (user, None)

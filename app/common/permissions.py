from rest_framework.permissions import BasePermission

from users.models import UserType


class IsLibraryUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == UserType.LIBRARY


class IsVisitor(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == UserType.VISITOR

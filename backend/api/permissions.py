from rest_framework import permissions
from rest_framework.permissions import SAFE_METHODS


class IsAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Разрешает чтение для всех, изменение для автора"""
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or request.user == obj.author

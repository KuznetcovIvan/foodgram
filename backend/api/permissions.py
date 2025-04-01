from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Разрешает чтение для всех, изменение для автора"""
    def has_object_permission(self, request, view, obj):
        return request.method == 'GET' or request.user == obj.author

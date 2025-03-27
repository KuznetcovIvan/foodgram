from django.db.models import BooleanField, Exists, OuterRef, Value
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from users.models import Subscription, User
from .serializers import UserSerializer, AvatarSerializer


class UserViewSet(DjoserUserViewSet):
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'retrieve':
            return (AllowAny(),)
        return super().get_permissions()

    def get_queryset(self):
        queryset = User.objects.all()
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(is_subscribed=Exists(
                Subscription.objects.filter(
                    subscriber=self.request.user,
                    subscribed_to=OuterRef('pk'))))
        else:
            queryset = queryset.annotate(is_subscribed=Value(
                False, output_field=BooleanField()))
        return queryset

    @action(methods=['get'], detail=False)
    def me(self, request, *args, **kwargs):
        return Response(self.get_serializer(
            self.get_queryset().get(id=request.user.id)).data)

    @action(methods=['put', 'delete'], detail=False, url_path='me/avatar/')
    def avatar(self, request, *args, **kwargs):
        user = self.get_queryset().get(id=request.user.id)
        if request.method == 'PUT':
            serializer = AvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'avatar': user.avatar}, status=status.HTTP_200_OK)
        if request.method == 'DELETE':
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

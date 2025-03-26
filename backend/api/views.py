from django.db.models import BooleanField, Exists, OuterRef, Value
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from users.models import Subscription, User
from .serializers import UserSerializer


class UserViewSet(DjoserUserViewSet):
    serializer_class = UserSerializer

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

    @action(methods=["get"], detail=False)
    def me(self, request, *args, **kwargs):
        return Response(self.get_serializer(
            self.get_queryset().get(id=request.user.id)).data)

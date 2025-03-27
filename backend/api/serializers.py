from rest_framework import serializers

from users.models import User
from .fields import Base64ImageField


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)

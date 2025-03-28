import random
import string

from django.db.models import BooleanField, Exists, OuterRef, Sum, Value
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from core.constants import LINK_LENGTH
from recipes.models import (Ingredient, Recipe, RecipeIngredient, ShoppingCart,
                            Tag)
from users.models import User

from .filters import RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeCreateUpdateSerializer, RecipeSerializer,
                          TagSerializer, UserSerializer)


def redirect_to_recipe(request, short_link):
    return redirect(reverse(
        'recipes-detail',
        kwargs={'pk': get_object_or_404(Recipe, short_link=short_link).pk}))


class UserViewSet(DjoserUserViewSet):
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action in ('retrieve', 'list'):
            return (AllowAny(),)
        return super().get_permissions()

    def get_queryset(self):
        queryset = User.objects.all()
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(is_subscribed=Exists(
                self.request.user.following.filter(
                    subscribed_to=OuterRef('pk'))))
        else:
            queryset = queryset.annotate(is_subscribed=Value(
                False, output_field=BooleanField()))
        return queryset

    @action(methods=('get',), detail=False)
    def me(self, request):
        return Response(self.get_serializer(
            self.get_queryset().get(id=request.user.id)).data)

    @action(methods=('put', 'delete'), detail=False, url_path='me/avatar')
    def avatar(self, request):
        user = self.get_queryset().get(id=request.user.id)
        if request.method == 'PUT':
            serializer = AvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': user.avatar.url}, status=status.HTTP_200_OK)
        if request.method == 'DELETE':
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    filter_backends = (DjangoFilterBackend,)
    filter_set_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_queryset(self):
        queryset = Recipe.objects.all()
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    self.request.user.favorites.filter(
                        recipe=OuterRef('pk'))),
                is_in_shopping_cart=Exists(
                    self.request.user.shopping_cart.filter(
                        recipe=OuterRef('pk'))))
        else:
            queryset = queryset.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField()))
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    @action(methods=('get',), detail=True, url_path='get-link')
    def get_short_link(self, request, pk):
        recipe = self.get_object()
        if recipe.short_link is None:
            while True:
                link = ''.join(random.choices(
                    string.digits + string.ascii_letters, k=LINK_LENGTH))
                if not Recipe.objects.filter(short_link=link).exists():
                    recipe.short_link = link
                    recipe.save(update_fields=('short_link',))
                    break
        absolute_uri = request.build_absolute_uri('/')
        short_link = f'{absolute_uri}s/{recipe.short_link}'
        return Response({"short-link": short_link}, status=status.HTTP_200_OK)

    @action(methods=('get',), detail=False,
            permission_classes=(IsAuthenticated,))
    def download_shopping_car(self, request):
        user_recipes_in_cart = (
            ShoppingCart.objects
            .filter(user=self.request.user)
            .values_list('recipe', flat=True)
        )
        ingredients = (
            RecipeIngredient.objects
            .filter(recipe__in=user_recipes_in_cart)
        )
        product_list = list(
            ingredients
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )

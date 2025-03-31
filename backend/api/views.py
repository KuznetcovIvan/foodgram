from datetime import datetime as dt

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import BooleanField, Exists, OuterRef, Sum, Value
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from core.utils import get_shopping_cart_pdf
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Subscription, User

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeSerializer,
                          RecipeUpdateSerializer, ShoppingCartSerializer,
                          TagSerializer, UserSerializer,
                          UserWithRecipesSerializer)


def redirect_to_recipe(request, pk):
    return redirect(reverse(
        'recipes-detail', kwargs={'pk': get_object_or_404(Recipe, pk=pk)}))


class UserViewSet(DjoserUserViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    def get_permissions(self):
        if self.action in ('retrieve', 'list'):
            return (AllowAny(),)
        return super().get_permissions()

    @action(methods=('GET',), detail=False)
    def me(self, request):
        return Response(self.get_serializer(
            self.get_queryset().get(id=request.user.id)).data)

    @action(methods=('PUT', 'DELETE'), detail=False, url_path='me/avatar')
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

    @action(methods=('GET',), detail=False,
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        subscriptions = self.get_queryset().prefetch_related('recipes').filter(
            id__in=Subscription.objects.filter(subscriber=request.user).values(
                'subscribed_to'))
        page = self.paginate_queryset(subscriptions)
        limit = request.query_params.get('recipes_limit')
        if page is not None:
            serializer = UserWithRecipesSerializer(
                page, many=True, context={'request': request})
            if limit:
                for user_data in serializer.data:
                    user_data['recipes'] = user_data['recipes'][:int(limit)]
            return self.get_paginated_response(serializer.data)
        serializer = UserWithRecipesSerializer(
            subscriptions, many=True, context={'request': request})
        if limit:
            for user_data in serializer.data:
                user_data['recipes'] = user_data['recipes'][:int(limit)]
        return Response(serializer.data)

    @action(methods=('POST', 'DELETE'),
            detail=True, permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id):
        user = self.request.user
        target_user = get_object_or_404(User, id=id)
        if user == target_user:
            return Response(
                {'detail': 'Нельзя подписаться на себя'},
                status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'POST':
            try:
                Subscription.objects.create(
                    subscriber=user, subscribed_to=target_user)
                limit = request.query_params.get('recipes_limit')
                serializer = UserWithRecipesSerializer(
                    target_user, context={'request': request})
                data = serializer.data
                if limit:
                    data['recipes'] = ShoppingCartSerializer(
                        target_user.recipes.all()[:int(limit)],
                        many=True,
                        context={'request': request}).data
                return Response(data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST)
        if request.method == 'DELETE':
            try:
                Subscription.objects.get(
                    subscriber=user, subscribed_to=target_user).delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except ObjectDoesNotExist:
                return Response(
                    {'detail': 'Вы не подписаны на этого пользователя'},
                    status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(ReadOnlyModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_queryset(self):
        queryset = (
            Recipe.objects
            .select_related('author')
            .prefetch_related('tags', 'recipe_ingredients__ingredient'))
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
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        elif self.action == 'update':
            return RecipeUpdateSerializer
        return RecipeSerializer

    @action(methods=('GET',), detail=True, url_path='get-link')
    def get_short_link(self, request, pk):
        return Response({'short-link': '{}s/{}'.format(
            request.build_absolute_uri('/'), self.get_object().id)},
            status=status.HTTP_200_OK)

    @action(methods=('GET',), detail=False,
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        user_recipes_in_cart = (
            ShoppingCart.objects
            .filter(user=self.request.user)
            .values_list('recipe', flat=True)
        )
        product_list = list(
            RecipeIngredient.objects
            .filter(recipe__in=user_recipes_in_cart)
            .values('ingredient__name', 'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
            .order_by('ingredient__name')
        )
        date = dt.now()
        return FileResponse(
            get_shopping_cart_pdf(product_list, date, request),
            as_attachment=True,
            filename='to_buy_{}.pdf'.format(date.strftime('%d_%m_%Y')))

    @action(methods=('POST', 'DELETE'), detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        recipe = self.get_object()
        if request.method == 'POST':
            try:
                ShoppingCart.objects.create(
                    user=self.request.user, recipe=recipe)
            except IntegrityError:
                return Response(
                    {'detail': 'Рецепт уже в списке покупок'},
                    status=status.HTTP_400_BAD_REQUEST)
            return Response(ShoppingCartSerializer(recipe).data,
                            status=status.HTTP_201_CREATED)
        try:
            ShoppingCart.objects.get(
                user=self.request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'detail': 'Рецепта нет в списке покупок'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=('POST', 'DELETE'), detail=True,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        recipe = self.get_object()
        if request.method == 'POST':
            try:
                Favorite.objects.create(
                    user=self.request.user, recipe=recipe)
                return Response(
                    ShoppingCartSerializer(recipe).data,
                    status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {'detail': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST)
        try:
            Favorite.objects.get(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'detail': 'Рецепта нет в избранном'},
                            status=status.HTTP_400_BAD_REQUEST)

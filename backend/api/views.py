from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import BooleanField, Exists, OuterRef, Sum, Value
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone as tz
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from recipes.utils import get_shopping_cart_pdf
from users.models import Subscription, User
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (AvatarSerializer, IngredientSerializer,
                          RecipeCreateSerializer, RecipeSerializer,
                          RecipeUpdateSerializer,
                          ShoppingCartFavoriteSerializer, TagSerializer,
                          UserSerializer, UserWithRecipesSerializer)


def redirect_to_recipe(request, pk):
    """Функция перенаправляет запрос с короткого адреса на основной"""
    return redirect('/recipes/{}/'.format(get_object_or_404(Recipe, pk=pk).pk))


class UserViewSet(DjoserUserViewSet):
    """ViewSet для пользователей и подписок"""
    serializer_class = UserSerializer

    def get_queryset(self):
        """Метод добавляет аннотацию is_subscribed"""
        user = self.request.user
        queryset = User.objects.all()
        if user.is_authenticated:
            queryset = queryset.annotate(
                is_subscribed=Exists(
                    Subscription.objects.filter(
                        subscriber=user, subscribed_to=OuterRef('id'))))
        else:
            queryset = queryset.annotate(
                is_subscribed=Value(False, output_field=BooleanField()))
        return queryset

    def get_permissions(self):
        """Разрешения: любые для чтения, стандартные для остальных"""
        if self.action in ('retrieve', 'list'):
            return (AllowAny(),)
        return super().get_permissions()

    @action(methods=('GET',), detail=False)
    def me(self, request):
        """Для возвращения данных пользователя"""
        return Response(self.get_serializer(
            self.get_queryset().get(id=request.user.id)).data)

    @action(methods=('PUT', 'DELETE'), detail=False, url_path='me/avatar')
    def avatar(self, request):
        """Добавляет или удаляет аватар пользователя"""
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
        """Список подписок пользователя"""
        subscriptions = self.get_queryset().prefetch_related('recipes').filter(
            id__in=Subscription.objects.filter(subscriber=request.user).values(
                'subscribed_to'))
        page = self.paginate_queryset(subscriptions)
        limit = self.request.query_params.get('recipes_limit')
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
        """Добавляет или удаляет подписку"""
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
                limit = self.request.query_params.get('recipes_limit')
                serializer = UserWithRecipesSerializer(
                    target_user, context={'request': request})
                data = serializer.data
                if limit:
                    data['recipes'] = ShoppingCartFavoriteSerializer(
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
    """ViewSet тегов"""
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """ViewSet ингредиентов"""
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    pagination_class = None
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """ViewSet для управления рецептами"""
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    permission_classes = (IsAuthorOrReadOnly,)

    def get_queryset(self):
        """Добавляет аннотации is_favorited и is_in_shopping_cart"""
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
        """Выбор сериализатора по действию"""
        if self.action in ('create', 'partial_update'):
            return RecipeCreateSerializer
        elif self.action == 'update':
            return RecipeUpdateSerializer
        return RecipeSerializer

    @action(methods=('GET',), detail=True, url_path='get-link')
    def get_short_link(self, request, pk):
        """Возвращает короткую ссылку на рецепт"""
        return Response({'short-link': '{}s/{}'.format(
            request.build_absolute_uri('/'), self.get_object().id)},
            status=status.HTTP_200_OK)

    @action(methods=('GET',), detail=False,
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """Для скачивания списка покупок в PDF"""
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
        date = tz.now()
        return FileResponse(
            get_shopping_cart_pdf(product_list, date, request),
            as_attachment=True,
            filename='shopping-list.pdf')

    def handle_recipe(self, request, model, exists_message, not_found_message):
        """Метод для добавления или удаления рецепта"""
        recipe = self.get_object()
        if request.method == 'POST':
            try:
                model.objects.create(user=request.user, recipe=recipe)
                return Response(
                    ShoppingCartFavoriteSerializer(recipe).data,
                    status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response(
                    {'detail': exists_message},
                    status=status.HTTP_400_BAD_REQUEST)
        try:
            model.objects.get(user=request.user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'detail': not_found_message},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=('POST', 'DELETE'), detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        """Управление списком покупок"""
        return self.handle_recipe(
            request,
            ShoppingCart,
            'Рецепт уже в списке покупок',
            'Рецепта нет в списке покупок')

    @action(methods=('POST', 'DELETE'), detail=True,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        """Управление списком избранного"""
        return self.handle_recipe(
            request,
            Favorite,
            'Рецепт уже в избранном',
            'Рецепта нет в избранном')

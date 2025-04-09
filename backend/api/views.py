from django.db.models import BooleanField, Exists, OuterRef, Sum, Value
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils import timezone as tz
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Subscription,
    Tag,
    User
)
from recipes.utils import get_shopping_cart_text
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    TagSerializer,
    UserSerializer,
    UserWithRecipesSerializer
)


class UserViewSet(DjoserUserViewSet):
    """ViewSet для пользователей и подписок"""
    serializer_class = UserSerializer

    def get_queryset(self):
        """Метод добавляет аннотацию is_subscribed"""
        user = self.request.user
        return User.objects.all().annotate(
            is_subscribed=Exists(
                Subscription.objects.filter(
                    subscriber=user, subscribed_to=OuterRef('id'))
            ) if user.is_authenticated else Value(
                False, output_field=BooleanField()))

    @action(
        methods=('GET',), detail=False, permission_classes=(IsAuthenticated,))
    def me(self, request):
        """Для возвращения данных пользователя"""
        return super().me(request)

    @action(methods=('PUT', 'DELETE'), detail=False, url_path='me/avatar',
            permission_classes=(IsAuthenticated,))
    def avatar(self, request):
        """Добавляет или удаляет аватар пользователя"""
        user = self.get_queryset().get(id=request.user.id)
        if request.method == 'PUT':
            serializer = AvatarSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                {'avatar': user.avatar.url}, status=status.HTTP_200_OK)
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('GET',), detail=False,
            permission_classes=(IsAuthenticated,))
    def subscriptions(self, request):
        """Список подписок пользователя"""
        subscriptions = self.get_queryset().prefetch_related('recipes').filter(
            id__in=Subscription.objects.filter(subscriber=request.user).values(
                'subscribed_to'))
        return self.get_paginated_response(
            UserWithRecipesSerializer(
                self.paginate_queryset(subscriptions),
                many=True,
                context={'request': request}).data)

    @action(methods=('POST', 'DELETE'),
            detail=True, permission_classes=(IsAuthenticated,))
    def subscribe(self, request, id):
        """Добавляет или удаляет подписку"""
        user = self.request.user
        author = get_object_or_404(User, id=id)
        if user == author:
            raise ValidationError(
                {'detail': 'Нельзя подписаться или отписаться от самого себя'})
        if request.method == 'POST':
            if Subscription.objects.filter(
                    subscriber=user, subscribed_to=author).exists():
                raise ValidationError(
                    {'detail': 'Вы уже подписаны на этого пользователя'})
            Subscription.objects.create(subscriber=user, subscribed_to=author)
            return Response(UserWithRecipesSerializer(
                author, context={'request': request}).data,
                status=status.HTTP_201_CREATED)
        get_object_or_404(
            Subscription, subscriber=user, subscribed_to=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
    queryset = Recipe.objects.all()

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
                    self.request.user.cart_items.filter(
                        recipe=OuterRef('pk'))))
        else:
            queryset = queryset.annotate(
                is_favorited=Value(False, output_field=BooleanField()),
                is_in_shopping_cart=Value(False, output_field=BooleanField()))
        return queryset

    def get_serializer_class(self):
        """Выбор сериализатора по действию"""
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeReadSerializer

    @action(methods=('GET',), detail=True, url_path='get-link')
    def get_short_link(self, request, pk):
        """Возвращает короткую ссылку на рецепт"""
        return Response({'short-link': request.build_absolute_uri(
            reverse('recipes:redirect-to-recipe', kwargs={'pk': pk}))})

    @action(methods=('GET',), detail=False,
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        """Для скачивания списка покупок"""
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
        recipes = Recipe.objects.filter(id__in=user_recipes_in_cart)
        date = tz.now().strftime('%d-%m-%Y')
        return HttpResponse(
            get_shopping_cart_text(product_list, recipes),
            content_type='text/plain',
            headers={'Content-Disposition':
                     f'attachment; filename="shopping-list-{date}.txt"'})

    def handle_recipe(self, request, model):
        """Метод для добавления или удаления рецепта"""
        recipe = self.get_object()
        if request.method == 'POST':
            if model.objects.filter(user=request.user, recipe=recipe).exists():
                raise ValidationError(
                    {'detail':
                        f'Рецепт уже добавлен в {model._meta.verbose_name}'})
            model.objects.create(user=request.user, recipe=recipe)
            return Response(
                RecipeShortSerializer(recipe).data,
                status=status.HTTP_201_CREATED)
        get_object_or_404(model, user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(methods=('POST', 'DELETE'), detail=True,
            permission_classes=(IsAuthenticated,))
    def shopping_cart(self, request, pk):
        """Управление списком покупок"""
        return self.handle_recipe(request, ShoppingCart)

    @action(methods=('POST', 'DELETE'), detail=True,
            permission_classes=(IsAuthenticated,))
    def favorite(self, request, pk):
        """Управление списком избранного"""
        return self.handle_recipe(request, Favorite)

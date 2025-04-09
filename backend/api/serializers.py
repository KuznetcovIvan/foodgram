from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.constants import (MAX_LENGTH_RECIPE_NAME, MIN_COOKING_TIME,
                               MIN_INGREDIENT_AMOUNT)
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User

from .fields import Base64ImageField


class UserSerializer(DjoserUserSerializer):
    """Сериализатор пользователя с подпиской"""
    is_subscribed = serializers.BooleanField(default=False, read_only=True)

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = (*DjoserUserSerializer.Meta.fields, 'is_subscribed', 'avatar')


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода краткой информации о рецепте"""
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class UserWithRecipesSerializer(UserSerializer):
    """Сериализатор пользователя с рецептами"""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)

    class Meta(UserSerializer.Meta):
        fields = (*UserSerializer.Meta.fields, 'recipes', 'recipes_count')

    def get_recipes(self, obj):
        """Получает рецепты с учетом лимита"""
        limit = self.context.get('request').query_params.get('recipes_limit')
        recipes = (obj.recipes.all()[:int(limit)]
                   if limit else obj.recipes.all())
        return RecipeShortSerializer(
            recipes, many=True, context=self.context).data


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор аватара c кастомным полем Base64ImageField"""
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор тегов"""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов"""

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор ингредиентов в рецепте для чтения"""
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор рецепта для чтения"""
    id = serializers.IntegerField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        source='recipe_ingredients', many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')
        read_only_fields = fields

    def get_is_favorited(self, recipe):
        user = self.context['request'].user
        return user.is_authenticated and user.favorites.filter(
            recipe=recipe).exists()

    def get_is_in_shopping_cart(self, recipe):
        user = self.context['request'].user
        return user.is_authenticated and user.cart_items.filter(
            recipe=recipe).exists()


class IngredientInRecipeReadSerializer(serializers.Serializer):
    """Сериализатор ингредиента для записи"""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор создания и изменения рецепта"""
    ingredients = IngredientInRecipeReadSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True)
    image = Base64ImageField(required=False)
    name = serializers.CharField(
        max_length=MAX_LENGTH_RECIPE_NAME, required=True)
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME, required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')

    def items_validate(self, items, name):
        """Проверяет список на пустоту и дубликаты"""
        if not items:
            raise serializers.ValidationError(
                f'Список {name} не может быть пустым')
        duplicates = [item for item in set(items) if items.count(item) > 1]
        if duplicates:
            raise serializers.ValidationError(
                f'В списке {name} имеются дубликаты: {duplicates}')
        return items

    def validate_ingredients(self, ingredients):
        """Проверка: ингредиенты не пустые и уникальные"""
        ingredient_ids = [ingredient['id'].id for ingredient in ingredients]
        self.items_validate(ingredient_ids, 'ингредиентов')
        return ingredients

    def validate_tags(self, tags):
        """Проверка: теги не пустые и уникальные"""
        return self.items_validate(tags, 'тегов')

    def validate(self, data):
        """Проверка на наличие  полей tags и ingredients"""
        if 'tags' not in data:
            raise serializers.ValidationError(
                'Поле tags отсутствует в запросе')
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                'Поле ingredients отсутствует в запросе')
        if self.context['request'].method == 'POST' and 'image' not in data:
            raise serializers.ValidationError(
                'Поле image обязательно для создания')
        return data

    def to_representation(self, instance):
        """После создания или обновления рецепта
        перенаправляет на RecipeReadSerializer"""
        return RecipeReadSerializer(instance, context=self.context).data

    def save_recipe(self, recipe, validated_data):
        """Метод для сохранения рецепта с тегами и ингредиентами"""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        if recipe.pk:
            recipe = super().update(recipe, validated_data)
        else:
            validated_data['author'] = self.context['request'].user
            recipe = super().create(validated_data)
        recipe.tags.set(tags)
        recipe.recipe_ingredients.all().delete()
        RecipeIngredient.objects.bulk_create(
            [RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount'])
                for ingredient in ingredients])
        return recipe

    def create(self, validated_data):
        """Создание нового рецепта"""
        return self.save_recipe(
            Recipe(author=self.context['request'].user), validated_data)

    def update(self, instance, validated_data):
        """Обновление рецепта"""
        return self.save_recipe(instance, validated_data)

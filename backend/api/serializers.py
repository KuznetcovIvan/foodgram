from rest_framework import serializers

from users.models import User
from recipes.models import Tag, Ingredient, Recipe, RecipeIngredient
from .fields import Base64ImageField
from core.constants import (MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT,
                            MAX_LENGTH_RECIPE_NAME)


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


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = '__all__'


class RecipeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = IngredientSerializer(many=True, read_only=True)
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')


class IngredientInRecipeSerializer(serializers.Serializer):
    """Сериализатор для добавления информации об ингредиенте в рецепте.
    Используется в RecipeCreateUpdateSerializer для структурирования
    и валидации данных об ингредиентах, которые передаются в запросах."""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True)
    image = Base64ImageField()
    name = serializers.CharField(max_length=MAX_LENGTH_RECIPE_NAME)
    text = serializers.CharField()
    cooking_time = serializers.IntegerField(min_value=MIN_COOKING_TIME)

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')
        read_only_fields = ('id',)

    def save_recipe(self, recipe, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        for attr, value in validated_data.items():
            setattr(recipe, attr, value)
        recipe.save()
        recipe.tags.set(tags_data)
        recipe.recipe_ingredients.all().delete()
        for ingredient in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
        return recipe

    def to_internal_value(self, data):
        data = dict(data)
        request = self.context.get('request')
        if request and request.method == 'PATCH' and 'image' not in data:
            data['image'] = self.instance.image
        return super().to_internal_value(data)

    def create(self, validated_data):
        recipe = Recipe(author=self.context['request'].user)
        return self.save_recipe(recipe, validated_data)

    def update(self, instance, validated_data):
        return self.save_recipe(instance, validated_data)


class RecipeGetShortLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('short_link',)

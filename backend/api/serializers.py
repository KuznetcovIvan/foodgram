from rest_framework import serializers

from core.constants import (MAX_LENGTH_RECIPE_NAME, MIN_COOKING_TIME,
                            MIN_INGREDIENT_AMOUNT)
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import User

from .fields import Base64ImageField


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'avatar')


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class UserWithRecipesSerializer(UserSerializer):
    recipes = ShoppingCartSerializer(
        many=True, read_only=True)
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')


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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True)
    amount = serializers.IntegerField(read_only=True)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredients', many=True, read_only=True)
    is_favorited = serializers.BooleanField(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time')


class IngredientInRecipeSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField(min_value=MIN_INGREDIENT_AMOUNT)


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, required=True)
    image = Base64ImageField(required=True)
    name = serializers.CharField(
        max_length=MAX_LENGTH_RECIPE_NAME, required=True)
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_COOKING_TIME, required=True)

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time')
        read_only_fields = ('id',)

    def validate_ingredients(self, ingredients):
        if not ingredients:
            raise serializers.ValidationError(
                'Список ингредиентов не может быть пустым')
        ingredient_ids = [ingredient['id'].id for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError(
                'Ингредиенты не должны повторяться')
        return ingredients

    def validate_tags(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Список тегов не может быть пустым')
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError('Теги не должны повторяться')
        return tags

    def validate(self, data):
        if 'tags' not in data:
            raise serializers.ValidationError(
                'Поле tags отсутствует в запросе')
        if 'ingredients' not in data:
            raise serializers.ValidationError(
                'Поле ingredients отсутствует в запросе')

        return data

    def to_representation(self, instance):
        instance.is_favorited = getattr(
            instance, 'is_favorited', False)
        instance.is_in_shopping_cart = getattr(
            instance, 'is_in_shopping_cart', False)
        return RecipeSerializer(instance, context=self.context).data

    def save_recipe(self, recipe, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        for attr, value in validated_data.items():
            setattr(recipe, attr, value)
        recipe.save()
        recipe.tags.set(tags)
        recipe.recipe_ingredients.all().delete()

        recipe_ingredients = [RecipeIngredient(
            recipe=recipe,
            ingredient=ingredient['id'],
            amount=ingredient['amount'])
            for ingredient in ingredients]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    def create(self, validated_data):
        recipe = Recipe(author=self.context['request'].user)
        return self.save_recipe(recipe, validated_data)

    def update(self, instance, validated_data):
        return self.save_recipe(instance, validated_data)


class RecipeUpdateSerializer(RecipeCreateSerializer):
    image = Base64ImageField(required=False)

    class Meta(RecipeCreateSerializer.Meta):
        pass

from django_filters import (ModelChoiceFilter, ModelMultipleChoiceFilter,
                            NumberFilter)
from django_filters.rest_framework import CharFilter, FilterSet

from recipes.models import Ingredient, Recipe, Tag
from users.models import User


class RecipeFilter(FilterSet):
    """Фильтр рецептов по избранному, корзине, автору и тегам"""
    is_favorited = NumberFilter()
    is_in_shopping_cart = NumberFilter()
    author = ModelChoiceFilter(queryset=User.objects.all(), to_field_name='id')
    tags = ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')


class IngredientFilter(FilterSet):
    """Фильтр ингредиентов по началу названия
    и совпадению в произвольном месте"""
    name = CharFilter(method='filter_name')

    class Meta:
        model = Ingredient
        fields = ('name',)

    def filter_name(self, ingredients, name, value):
        if value:
            return (ingredients.filter(name__istartswith=value)
                    | ingredients.filter(name__icontains=value)
                    .exclude(name__istartswith=value))
        return ingredients

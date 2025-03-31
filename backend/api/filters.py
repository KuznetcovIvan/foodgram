from django_filters import (ModelChoiceFilter, ModelMultipleChoiceFilter,
                            NumberFilter)
from django_filters.rest_framework import CharFilter, FilterSet

from recipes.models import Ingredient, Recipe, Tag
from users.models import User


class RecipeFilter(FilterSet):
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
    name = CharFilter(field_name='name', lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ('name',)

from .admin_filters import CookingTimeFilter, RecipesFilter
from django.contrib.admin import ModelAdmin, TabularInline, display, register
from django.utils.safestring import mark_safe

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class RecipeCountMixin:
    """Миксин для показа числа рецептов"""
    @display(description='Число рецептов')
    def get_recipe_count(self, tag_or_ingredient):
        return tag_or_ingredient.recipes.count()


class RecipeIngredientInline(TabularInline):
    """Инлайн для инградиентов"""
    model = RecipeIngredient
    extra = 1
    min_num = 1


@register(Tag)
class TagAdmin(ModelAdmin, RecipeCountMixin):
    """Класс для управления моделью тегов в админ-панели"""
    list_display = ('name', 'slug', 'get_recipe_count')
    search_fields = ('name', 'slug')


@register(Ingredient)
class IngredientAdmin(ModelAdmin, RecipeCountMixin):
    """Класс для управления моделью инградиентов в админ-панели"""
    list_display = ('name', 'measurement_unit', 'get_recipe_count')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit', RecipesFilter)


@register(Recipe)
class RecipeAdmin(ModelAdmin):
    """Класс для управления моделью рецептов в админ-панели"""
    list_display = (
        'id', 'name', 'cooking_time', 'author', 'get_tags',
        'get_favorite_count', 'get_ingredients', 'get_image'
    )
    search_fields = ('name', 'author__username', 'tags__name')
    list_filter = ('tags', 'author', CookingTimeFilter)
    inlines = (RecipeIngredientInline,)
    filter_horizontal = ('tags',)

    @display(description='Теги')
    @mark_safe
    def get_tags(self, recipe):
        """Метод отображает теги рецепта"""
        return '<br>'.join(f'<span style="color: black;">{tag.name}</span>'
                           for tag in recipe.tags.all())

    @display(description='В избранном')
    def get_favorite_count(self, recipe):
        """Метод возвращает число добавлений рецепта в избранное"""
        return recipe.favorites.count()

    @display(description='Продукты')
    @mark_safe
    def get_ingredients(self, recipe):
        'Метод для отображения ингредиентов рецепта'
        return '<br>'.join(f'{ing.ingredient.name} - {ing.amount} '
                           f'{ing.ingredient.measurement_unit}'
                           for ing in recipe.recipe_ingredients.all())

    @display(description='Картинка')
    @mark_safe
    def get_image(self, recipe):
        'Метод для отображения картинки рецепта'
        return f'<img src="{recipe.image.url}" style="max-height: 100px;">'


@register(Favorite, ShoppingCart)
class FavoriteShoppingCartAdmin(ModelAdmin):
    'Класс для управления моделями избранного и корзины в админ-панели'
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')

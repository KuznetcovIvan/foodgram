from django.contrib import admin

from .models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                     ShoppingCart, Tag)


class RecipeIngredientInline(admin.TabularInline):
    """Инлайн для инградиентов"""
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Класс для управления моделью тегов в админ-панели"""
    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Класс для управления моделью инградиентов в админ-панели"""
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Класс для управления моделью рецептов в админ-панели"""
    list_display = ('name', 'author', 'get_favorite_count')
    search_fields = ('name', 'author__username')
    list_filter = ('tags',)
    inlines = (RecipeIngredientInline,)
    filter_horizontal = ('tags',)

    def get_favorite_count(self, obj):
        """Метод возвращает число добавлений рецепта в избранное"""
        return obj.favorited_by.count()
    get_favorite_count.short_description = 'В избранном'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Класс для управления моделью избранного в админ-панели"""
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Класс для управления моделью корзины в админ-панели"""
    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    list_filter = ('user', 'recipe')

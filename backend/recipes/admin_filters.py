from django.contrib.admin import SimpleListFilter

from .models import Recipe


class BaseFilter(SimpleListFilter):
    """Базовый класс для фильтров"""
    title = ''
    parameter_name = ''
    relation_field = ''
    LOOKUPS = (('yes', 'Да'), ('no', 'Нет'))

    def lookups(self, request, model_admin):
        return self.LOOKUPS

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(
                **{f'{self.relation_field}__isnull': False}).distinct()
        if self.value() == 'no':
            return queryset.filter(**{f'{self.relation_field}__isnull': True})
        return queryset


class RecipesFilter(BaseFilter):
    """Фильтр наличия рецептов"""
    title = 'Есть рецепты'
    parameter_name = 'has_recipes'
    relation_field = 'recipes'


class SubscriptionsFilter(BaseFilter):
    """Фильтр по наличию подписок"""
    title = 'Есть подписки'
    parameter_name = 'has_subscriptions'
    relation_field = 'subscribers'


class FollowersFilter(BaseFilter):
    """Фильтр по наличию подписчиков"""
    title = 'Есть подписчики'
    parameter_name = 'has_followers'
    relation_field = 'authors'


class CookingTimeFilter(SimpleListFilter):
    """Фильтр по времени готовки"""
    title = 'Время готовки'
    parameter_name = 'cooking_time'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ranges = None
        self.fast = None
        self.medium = None

    def set_ranges(self):
        """Определяет диапазоны времени готовки и сохраняет их в экземпляре"""
        times = Recipe.objects.values_list('cooking_time', flat=True)
        if len(set(times)) < 3:
            return
        max_time = max(times)
        self.fast = max_time // 3
        self.medium = (2 * max_time) // 3
        self.ranges = {
            'fast': (0, self.fast),
            'medium': (self.fast + 1, self.medium),
            'long': (self.medium + 1, max_time)
        }

    def filter_by_range(self, key, recipes=None):
        """Фильтрация рецептов по диапазону времени готовки"""
        recipes = recipes or Recipe.objects
        return recipes.filter(cooking_time__range=self.ranges[key])

    def lookups(self, request, model_admin):
        self.set_ranges()
        if not self.ranges:
            return []
        return (
            (
                'fast',
                f'Быстрее {self.fast} мин '
                f'({self.filter_by_range("fast").count()})'
            ),
            (
                'medium',
                f'Быстрее {self.medium} мин '
                f'({self.filter_by_range("medium").count()})'
            ),
            (
                'long',
                f'Долго '
                f'({self.filter_by_range("long").count()})'
            ),
        )

    def queryset(self, request, recipes):
        self.set_ranges()
        if not self.value():
            return recipes
        return self.filter_by_range(self.value(), recipes)

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
        self.time_ranges = None

    def get_time_ranges(self):
        """Возвращает словарь диапазонов времени готовки"""
        times = Recipe.objects.values_list('cooking_time', flat=True)
        if len(set(times)) <= 1:
            return None
        max_time = max(times)
        fast_threshold = max_time // 3
        medium_threshold = (2 * max_time) // 3
        return {
            'fast': (0, fast_threshold),
            'medium': (fast_threshold + 1, medium_threshold),
            'long': (medium_threshold + 1, max_time)}

    def filter_by_range(self, recipes, time_range):
        """Фильтрация рецептов по диапазону времени готовки"""
        return recipes.filter(cooking_time__range=time_range)

    def lookups(self, request, model_admin):
        self.time_ranges = self.get_time_ranges()
        if not self.time_ranges:
            return None
        fast_count = self.filter_by_range(
            Recipe.objects, self.time_ranges['fast']).count()
        medium_count = self.filter_by_range(
            Recipe.objects, self.time_ranges['medium']).count()
        long_count = self.filter_by_range(
            Recipe.objects, self.time_ranges['long']).count()
        fast_threshold = self.time_ranges['fast'][1]
        medium_threshold = self.time_ranges['medium'][1]
        return (
            ('fast', f'Быстрее {fast_threshold} мин ({fast_count})'),
            ('medium', f'Быстрее {medium_threshold} мин ({medium_count})'),
            ('long', f'Долго ({long_count})'),)

    def queryset(self, request, recipes):
        if not self.value():
            return recipes
        return self.filter_by_range(recipes, self.time_ranges[self.value()])

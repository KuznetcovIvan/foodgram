from django.contrib.admin import SimpleListFilter

from .models import Recipe


class BaseFilter(SimpleListFilter):
    """Базовый класс для фильтров"""
    title = ''
    parameter_name = ''
    relation_field = ''

    def lookups(self, request, model_admin):
        return (('yes', 'Да'), ('no', 'Нет'))

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

    def get_max_times_and_thresholds(self):
        times = Recipe.objects.values_list('cooking_time', flat=True)
        if not times:
            return None, None, None
        max_times = max(times)
        fast_threshold = int(max_times / 3)
        medium_threshold = int(2 * max_times / 3)
        return max_times, fast_threshold, medium_threshold

    def lookups(self, request, model_admin):
        max_times, fast_threshold, medium_threshold = (
            self.get_max_times_and_thresholds())
        if max_times is None:
            return None
        fast_count = Recipe.objects.filter(
            cooking_time__lte=fast_threshold).count()
        medium_count = Recipe.objects.filter(
            cooking_time__gt=fast_threshold,
            cooking_time__lte=medium_threshold).count()
        long_count = Recipe.objects.filter(
            cooking_time__gt=medium_threshold).count()
        return (
            ('fast', f'Быстрее {fast_threshold} мин ({fast_count})'),
            ('medium', f'Быстрее {medium_threshold} мин ({medium_count})'),
            ('long', f'Долго ({long_count})'))

    def queryset(self, request, queryset):
        _, fast_threshold, medium_threshold = (
            self.get_max_times_and_thresholds())
        if self.value() == 'fast':
            return queryset.filter(cooking_time__lte=fast_threshold)
        if self.value() == 'medium':
            return queryset.filter(
                cooking_time__gt=fast_threshold,
                cooking_time__lte=medium_threshold)
        if self.value() == 'long':
            return queryset.filter(cooking_time__gt=medium_threshold)
        return queryset

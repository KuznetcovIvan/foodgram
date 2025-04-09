from django.conf import settings
from django.contrib.admin import ModelAdmin, display, register, site
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from .models import Subscription, User
from recipes.admin_filters import (
    RecipesFilter, SubscriptionsFilter, FollowersFilter)
site.site_header = 'Администрирование Foodgram'
site.site_title = 'Foodgram Администрирование'
site.index_title = 'Добро пожаловать в панель управления Foodgram'
site.empty_value_display = 'Не задано'


@register(User)
class ExtendedUserAdmin(UserAdmin):
    """Класс для управления моделью пользователя в админ-панели"""
    list_display = (
        'id', 'username', 'full_name', 'email', 'avatar_thumbnail',
        'recipe_count', 'subscription_count', 'follower_count')

    search_fields = ('email', 'username')
    list_filter = (RecipesFilter, SubscriptionsFilter, FollowersFilter)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('first_name',
         'last_name', 'avatar', 'avatar_preview')}),
        ('Permissions', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': (
        'username', 'email', 'password1', 'password2',
        'first_name', 'last_name', 'avatar')}),)
    readonly_fields = ('avatar_preview',)

    @display(description='Полное имя')
    def full_name(self, user):
        return f'{user.first_name} {user.last_name}'

    @mark_safe
    def get_avatar(self, user, max_width):
        """Метод возвращает HTML-код для отображения аватара пользователя"""
        src = (user.avatar.url if user.avatar else settings.DEFAULT_AVATAR_URL)
        return (f'<img src="{src}" style="max-width: {max_width}; '
                f'height: auto;"alt="Avatar" />')

    @display(description='Аватар')
    def avatar_thumbnail(self, user):
        """Метод возвращает уменьшенную версию аватара
        для отображения в списке пользователей"""
        return self.get_avatar(user, '50px')

    @display(description='Предпросмотр')
    def avatar_preview(self, user):
        """Метод возвращает увеличенную версию аватара
        для предварительного просмотра"""
        return self.get_avatar(user, '200px')

    @display(description='Рецепты')
    def recipe_count(self, user):
        """Метод возвращает количество рецептов пользователя"""
        return user.recipes.count()

    @display(description='Подписки')
    def subscription_count(self, user):
        """Метод возвращает количество подписок пользователя"""
        return user.subscribers.count()

    @display(description='Подписчики')
    def follower_count(self, user):
        """Метод возвращает количество подписчиков пользователя"""
        return user.authors.count()


@register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    """Класс для управления моделью подписок в админ-панели"""
    list_display = ('subscriber', 'subscribed_to')
    search_fields = ('subscriber__username', 'subscribed_to__username')

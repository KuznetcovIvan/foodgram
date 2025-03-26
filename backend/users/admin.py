from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import Subscription, User

admin.site.site_header = 'Администрирование Foodgram'
admin.site.site_title = 'Foodgram Администрирование'
admin.site.index_title = 'Добро пожаловать в панель управления Foodgram'
admin.site.empty_value_display = 'Не задано'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Класс для управления моделью пользователя в админ-панели"""
    list_display = ('username', 'email', 'first_name',
                    'last_name', 'avatar_thumbnail')
    search_fields = ('email', 'username')
    list_filter = ('email', 'username')
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

    def get_avatar(self, obj, max_width):
        """Метод возвращает HTML-код для отображения аватара пользователя"""
        src = (obj.avatar.url if obj.avatar
               else '/static/admin/img/default-avatar.png')
        return format_html(
            '''<img src="{}" style="max-width: {};
            height: auto;"alt="Avatar" />''', src, max_width)

    def avatar_thumbnail(self, obj):
        """Метод возвращает уменьшенную версию аватара
        для отображения в списке пользователей"""
        return self.get_avatar(obj, '50px')
    avatar_thumbnail.short_description = 'Аватар'

    def avatar_preview(self, obj):
        """Метод возвращает увеличенную версию аватара
        для предварительного просмотра"""
        return self.get_avatar(obj, '200px')
    avatar_preview.short_description = 'Предпросмотр'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    """Класс для управления моделью подписок в админ-панели"""
    list_display = ('subscriber', 'subscribed_to', 'created_at')
    search_fields = ('subscriber__username', 'subscribed_to__username')
    list_filter = ('created_at',)

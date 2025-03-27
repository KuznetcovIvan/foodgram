from django.contrib.auth.models import AbstractUser
from django.db import models

from .utils import truncate_string


class User(AbstractUser):
    """Модель пользователя"""
    email = models.EmailField('Электронная почта', max_length=254, unique=True)
    username = models.CharField('Никнейм', max_length=150, unique=True)
    first_name = models.CharField('Имя', max_length=150)
    last_name = models.CharField('Фамилия', max_length=150)
    avatar = models.ImageField(
        'Аватар', upload_to='users/avatars/', blank=True, null=True,)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return truncate_string(self.username, 20)


class Subscription(models.Model):
    """Модель подписки"""
    subscriber = models.ForeignKey(
        User,
        related_name='following',
        verbose_name='Подписчик',
        on_delete=models.CASCADE
    )
    subscribed_to = models.ForeignKey(
        User,
        related_name='followers',
        verbose_name='На кого подписан',
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата подписки')

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('-created_at',)
        constraints = [models.UniqueConstraint(
            fields=['subscriber', 'subscribed_to'],
            name='unique_subscription')
        ]

    def __str__(self):
        return f'{self.subscriber} подписан на {self.subscribed_to}'

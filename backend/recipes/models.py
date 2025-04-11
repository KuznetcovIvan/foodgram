from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from .constants import (
    MAX_LENGTH_RECIPE_NAME,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT
)


class User(AbstractUser):
    """Модель пользователя"""
    email = models.EmailField('Электронная почта', max_length=254, unique=True)
    username = models.CharField('Никнейм', max_length=150, unique=True,
                                validators=(RegexValidator(r'^[\w.@+-]+\Z'),))
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
        return self.username[:20]


class Subscription(models.Model):
    """Модель подписки пользователя"""
    subscriber = models.ForeignKey(
        User,
        related_name='subscribers',
        verbose_name='Подписчик',
        on_delete=models.CASCADE
    )
    subscribed_to = models.ForeignKey(
        User,
        related_name='authors',
        verbose_name='На кого подписан',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('subscriber', 'subscribed_to')
        constraints = [models.UniqueConstraint(
            fields=['subscriber', 'subscribed_to'],
            name='unique_subscription')]

    def __str__(self):
        return f'{self.subscriber} подписан на {self.subscribed_to}'


class Tag(models.Model):
    """Модель тега"""
    name = models.CharField('Название', max_length=32, unique=True)
    slug = models.SlugField('Слаг', max_length=32, unique=True)

    class Meta:
        verbose_name = 'тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента"""
    name = models.CharField('Название', max_length=128, unique=True)
    measurement_unit = models.CharField('Единица измерения', max_length=64)

    class Meta:
        verbose_name = 'продукт'
        verbose_name_plural = 'Продукты'
        ordering = ('name',)
        constraints = [models.UniqueConstraint(
            fields=['name', 'measurement_unit'],
            name='unique_ingredient')]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(
        User, verbose_name='Автор', on_delete=models.CASCADE)
    name = models.CharField('Название', max_length=MAX_LENGTH_RECIPE_NAME)
    image = models.ImageField('Изображение', upload_to='recipes/images/')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient', verbose_name='Ингредиенты')
    tags = models.ManyToManyField(Tag, verbose_name='Теги')
    cooking_time = models.PositiveIntegerField(
        'Время (мин)',
        validators=(MinValueValidator(MIN_COOKING_TIME),))
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        default_related_name = 'recipes'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name[:40]


class RecipeIngredient(models.Model):
    """Модель связи рецепта и ингредиента c указанием количества"""
    recipe = models.ForeignKey(
        Recipe, verbose_name='Рецепт', on_delete=models.CASCADE)
    ingredient = models.ForeignKey(
        Ingredient, verbose_name='Ингредиент', on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(
        'Мера', validators=[MinValueValidator(MIN_INGREDIENT_AMOUNT)])

    class Meta:
        verbose_name = 'продукт в рецепте'
        verbose_name_plural = 'Продукты в рецепте'
        default_related_name = 'recipe_ingredients'
        constraints = [models.UniqueConstraint(
            fields=['recipe', 'ingredient'],
            name='unique_recipe_ingredient')]

    def __str__(self):
        return f'В рецепте {self.recipe} - {self.amount} {self.ingredient}'


class UserRecipeBaseModel(models.Model):
    """Базовый класс для связи пользователя c рецептами"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь')
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, verbose_name='Рецепт')

    class Meta:
        abstract = True
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_%(class)s_user_recipe')]

    def __str__(self):
        return f'{self.user} добавил {self.recipe}'


class Favorite(UserRecipeBaseModel):
    """Модель связи пользователя и избранных рецептов"""
    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        default_related_name = 'favorites'


class ShoppingCart(UserRecipeBaseModel):
    """Модель связи пользователя и рецептов в списке покупок"""
    class Meta(UserRecipeBaseModel.Meta):
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        default_related_name = 'cart_items'

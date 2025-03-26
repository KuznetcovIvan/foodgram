from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models

from core.utils import truncate_string

User = get_user_model()


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
    name = models.CharField('Название', max_length=32, unique=True)
    measurement_unit = models.CharField('Единица измерения', max_length=64)

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [models.UniqueConstraint(
            fields=['name', 'measurement_unit'],
            name='unique_ingredient')
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель рецепта"""
    author = models.ForeignKey(
        'users.User',
        related_name='recipes',
        verbose_name='Автор',
        on_delete=models.CASCADE
    )
    name = models.CharField('Название', max_length=256)
    image = models.ImageField('Изображение', upload_to='recipes/images/')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='used_in_recipes',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления (в минутах)',
        validators=[MinValueValidator(1)]
    )
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)

    class Meta:
        verbose_name = 'рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return truncate_string(self.name, 32)


class RecipeIngredient(models.Model):
    """Модель связи рецепта и ингредиента c указанием количества"""
    recipe = models.ForeignKey(
        Recipe,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
        on_delete=models.CASCADE
    )
    ingredient = models.ForeignKey(
        Ingredient,
        related_name='recipe_entries',
        verbose_name='Ингредиент',
        on_delete=models.CASCADE
    )
    amount = models.PositiveIntegerField(
        'Количество',
        validators=[MinValueValidator(1)]
    )

    class Meta:
        verbose_name = 'ингредиент'
        verbose_name_plural = 'Ингредиенты'
        constraints = [models.UniqueConstraint(
            fields=['recipe', 'ingredient'],
            name='unique_recipe_ingredient')
        ]

    def __str__(self):
        return f'В рецепте {self.recipe} - {self.amount} {self.ingredient}'


class Favorite(models.Model):
    """Модель избранного пользователя"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепт'
    )

    class Meta:
        verbose_name = 'избранное'
        verbose_name_plural = 'Избранное'
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_favorite')
        ]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное'


class ShoppingCart(models.Model):
    """Модель списка покупок пользователя"""
    user = models.ForeignKey(
        User,
        related_name='shopping_cart',
        verbose_name='Пользователь',
        on_delete=models.CASCADE,
    )
    recipe = models.ForeignKey(
        Recipe,
        related_name='in_shopping_cart',
        verbose_name='Рецепт',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [models.UniqueConstraint(
            fields=['user', 'recipe'],
            name='unique_shopping_cart')
        ]

    def __str__(self):
        return f"{self.user} добавил {self.recipe} в список покупок"

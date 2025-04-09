from babel.dates import format_date
from django.utils import timezone as tz


def get_shopping_cart_text(product_list, recipes):
    """Генерирует текст со списком покупок"""
    date = format_date(tz.now(), format='d MMMM yyyy', locale='ru')
    return '\n'.join([
        f'Список продуктов к покупке на {date} г.:',
        *[f'{index}. {product["ingredient__name"].capitalize()} - '
          f'{product["total_amount"]} '
          f'{product["ingredient__measurement_unit"]}.'
          for index, product in enumerate(product_list, start=1)],
        '=' * 50,
        'Составлен на основании рецептов:',
        *[f'{index}. {recipe.name} (автор: {recipe.author.username})'
          for index, recipe in enumerate(recipes, start=1)]])

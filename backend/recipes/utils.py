from babel.dates import format_date
from django.utils import timezone as tz

SHOPPING_CART_TEMPLATE = (
    'Список продуктов к покупке на {date} г.:\n'
    '{products}\n'
    '...\n'
    'Составлен на основании рецептов:\n'
    '{recipes}'
)
UNIT_SHORTCUTS = {
    'банка': 'бан', 'батон': 'бат', 'веточка': 'вет',
    'горсть': 'гор', 'капля': 'кап', 'кусок': 'кус',
    'стакан': 'стак', 'щепотка': 'щеп'
}


def get_shopping_cart_text(product_list, recipes):
    """Генерирует текст со списком покупок"""
    date = format_date(tz.now(), format='d MMMM yyyy', locale='ru')
    products = '\n'.join(['{}. {} - {} {}.'.format(
        index,
        product['ingredient__name'].capitalize(),
        product['total_amount'],
        UNIT_SHORTCUTS.get(product['ingredient__measurement_unit'],
                           product['ingredient__measurement_unit']))
        for index, product in enumerate(product_list, start=1)])
    recipes_list = '\n'.join(['{}. {} (@{})'.format(
        index,
        recipe.name,
        recipe.author.username)
        for index, recipe in enumerate(recipes, start=1)])
    return SHOPPING_CART_TEMPLATE.format(
        date=date, products=products, recipes=recipes_list)

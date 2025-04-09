from recipes.models import Ingredient

from ._base import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Импорт ингредиентов из JSON'

    def handle(self, *args, **options):
        path = options['path']
        self.stdout.write(f'Импорт ингредиентов из {path}')
        self.import_data(
            'ingredients.json', Ingredient, ['name', 'measurement_unit'])
        self.stdout.write(self.style.SUCCESS('Импорт ингредиентов завершен'))

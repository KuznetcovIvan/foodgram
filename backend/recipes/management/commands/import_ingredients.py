from recipes.models import Ingredient

from ._base import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Импорт ингредиентов из JSON'
    file_name = 'ingredients.json'
    model = Ingredient
    fields = ['name', 'measurement_unit']

    def handle(self, *args, **options):
        path = options['path']
        self.stdout.write(f'Импорт ингредиентов из {path}')
        self.import_data(self.file_name, self.model, self.fields)
        self.stdout.write(self.style.SUCCESS('Импорт ингредиентов завершен'))

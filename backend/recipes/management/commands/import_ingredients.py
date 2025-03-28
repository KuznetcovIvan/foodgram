from django.db.utils import IntegrityError

from recipes.models import Ingredient

from ._base import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Импорт ингредиентов из CSV'

    def handle(self, *args, **options):
        path = options['path']
        self.stdout.write(f'Импорт ингредиентов из {path}')
        self.import_data('ingredients.csv', ['name', 'measurement_unit'])
        self.stdout.write(self.style.SUCCESS('Импорт ингредиентов завершен'))

    def process_row(self, row, fields):
        try:
            data = {key: row[key] for key in fields if key in row}
            ingredient = Ingredient(
                name=data['name'], measurement_unit=data['measurement_unit'])
            ingredient.save()
            return ingredient
        except IntegrityError:
            self.stdout.write(self.style.WARNING(
                f'Ингредиент "{data["name"]}" уже существует и был пропущен'))
        except KeyError as e:
            self.stdout.write(self.style.WARNING(
                f'Некорректные данные: отсутствует поле {e}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'Ошибка обработки строки: {e}'))
        return None

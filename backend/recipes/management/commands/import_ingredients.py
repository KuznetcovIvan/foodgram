import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from recipes.models import Ingredient

DATA_PATH = os.path.join(settings.BASE_DIR, 'data')


class Command(BaseCommand):
    help = 'Импорт ингредиентов из CSV файла'

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=DATA_PATH)

    def handle(self, *args, **options):
        path = options['path']
        self.stdout.write(f'Импорт ингредиентов из {path}')
        self.import_data('ingredients.csv', ['name', 'measurement_unit'])
        self.stdout.write(self.style.SUCCESS('Импорт ингредиентов завершен'))

    def open_csv_file(self, file_name):
        file_path = os.path.join(DATA_PATH, file_name)
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.WARNING(f'Файл {file_name} не найден'))
            return
        try:
            return open(file_path, encoding='utf-8')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при чтении {file_name}: {e}'))
            return

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

    def import_data(self, file_name, fields):
        file = self.open_csv_file(file_name)
        if file is None:
            return
        with file:
            reader = csv.DictReader(file)
            for row in reader:
                self.process_row(row, fields)

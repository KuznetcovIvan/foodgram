import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

DATA_PATH = os.path.join(settings.BASE_DIR, 'data')


class BaseImportCommand(BaseCommand):
    """Базовый класс для импорта данных из JSON"""

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=DATA_PATH)

    def open_file(self, file_name):
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

    def import_data(self, file_name, model, fields):
        file = self.open_file(file_name)
        if file is None:
            return
        with file:
            try:
                objects = [model(**{key: row[key] for key in fields
                                    if key in row}) for row in json.load(file)]
                model.objects.bulk_create(objects, ignore_conflicts=True)
            except Exception as e:
                self.stdout.write(self.style.WARNING(
                    f'Ошибка обработки файла {file_name}: {e}'))

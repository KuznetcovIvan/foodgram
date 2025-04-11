import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

DATA_PATH = os.path.join(settings.BASE_DIR, 'data')


class BaseImportCommand(BaseCommand):
    """Базовый класс для импорта данных из JSON"""

    def add_arguments(self, parser):
        parser.add_argument('--path', type=str, default=DATA_PATH)

    def import_data(self, file_name, model, fields):
        file_path = os.path.join(DATA_PATH, file_name)
        try:
            with open(file_path, encoding='utf-8') as file:
                created_objects = model.objects.bulk_create(
                    (model(**row) for row in json.load(file)),
                    ignore_conflicts=True)
            self.stdout.write(self.style.SUCCESS(
                f'Импортировано {len(created_objects)} записей из {file_name}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Ошибка обработки файла {file_name}: {e}'))

from django.db.utils import IntegrityError

from recipes.models import Tag

from ._base import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Импорт тегов из CSV'

    def handle(self, *args, **options):
        path = options['path']
        self.stdout.write(f'Импорт тегов из {path}')
        self.import_data('tags.csv', ['name', 'slug'])
        self.stdout.write(self.style.SUCCESS('Импорт тегов завершен'))

    def process_row(self, row, fields):
        try:
            data = {key: row[key] for key in fields if key in row}
            tag = Tag(name=data['name'], slug=data['slug'])
            tag.save()
            return tag
        except IntegrityError:
            self.stdout.write(self.style.WARNING(
                f'Тег "{data["name"]}" уже существует и был пропущен'))
        except KeyError as e:
            self.stdout.write(self.style.WARNING(
                f'Некорректные данные: отсутствует поле {e}'))
        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f'Ошибка обработки строки: {e}'))
        return None

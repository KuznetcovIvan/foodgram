from recipes.models import Tag

from ._base import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Импорт тегов из JSON'

    def handle(self, *args, **options):
        path = options['path']
        self.stdout.write(f'Импорт тегов из {path}')
        self.import_data('tags.json', Tag, ['name', 'slug'])
        self.stdout.write(self.style.SUCCESS('Импорт тегов завершен'))

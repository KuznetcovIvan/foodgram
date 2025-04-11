from recipes.models import Tag

from ._base import BaseImportCommand


class Command(BaseImportCommand):
    help = 'Импорт тегов из JSON'
    file_name = 'tags.json'
    model = Tag
    fields = ['name', 'slug']

    def handle(self, *args, **options):
        path = options['path']
        self.stdout.write(f'Импорт тегов из {path}')
        self.import_data(self.file_name, self.model, self.fields)
        self.stdout.write(self.style.SUCCESS('Импорт тегов завершен'))

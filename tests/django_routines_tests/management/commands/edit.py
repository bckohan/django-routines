from .track import Command as TrackCommand
from ...models import TestModel


class Command(TrackCommand):
    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("name", type=str)

    def handle(self, *args, **options):
        super().handle(*args, **options)
        TestModel.objects.update_or_create(
            id=options["id"], defaults={"name": options["name"]}
        )

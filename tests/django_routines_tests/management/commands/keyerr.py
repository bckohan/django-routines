import typing as t
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options) -> t.Optional[str]:
        raise KeyError()

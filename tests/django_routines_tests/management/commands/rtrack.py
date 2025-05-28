from .track import Command as TrackCommand


class Command(TrackCommand):
    def handle(self, *args, **options) -> str:
        super().handle(*args, **options)
        return str(options["id"])

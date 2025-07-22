import typing as t
from django.core.management import BaseCommand
from tests import track_file
import json


invoked = []
passed_options = []


class TestError(Exception):
    pass


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("id", type=int)
        parser.add_argument("--demo", type=int)
        parser.add_argument("--flag", action="store_true", default=False)
        parser.add_argument("--raise", action="store_true", default=False)

    def handle(self, *args, **options) -> t.Optional[str]:
        global invoked
        global passed_options
        invoked.append(options["id"])
        passed_options.append(options)
        if not track_file.is_file():
            track_file.write_text(
                json.dumps({"invoked": [], "passed_options": []}, indent=4)
            )
        track = json.loads(track_file.read_text())
        track["invoked"].append(options["id"])
        track["passed_options"].append(options)
        track_file.write_text(json.dumps(track, indent=4))
        if options["raise"]:
            raise TestError("Kill the op.")
        return str(options["id"])

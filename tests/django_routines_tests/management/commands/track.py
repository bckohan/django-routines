from django.core.management import BaseCommand


invoked = []
passed_options = []


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("id", type=int)
        parser.add_argument("--demo", type=int)

    def handle(self, *args, **options):
        global invoked
        global passed_options
        invoked.append(options["id"])
        passed_options.append(options)

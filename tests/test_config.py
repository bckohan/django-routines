from django_typer.management import get_command
from django.test import TestCase, override_settings
from django.core.exceptions import ImproperlyConfigured
from django_routines import get_routine


class TestBadConfig(TestCase):
    @override_settings(
        DJANGO_ROUTINES={
            "no_name": {
                "commands": [
                    {"command": ("track", "0")},
                    {"command": ("does_not_exist",)},
                    {"command": ("track", "1")},
                ],
                "help_text": "Bad command test routine",
            },
            # "hyphen-name": {
            #     "commands": [
            #         {"command": ("track", "0")},
            #         {"command": ("does_not_exist",)},
            #         {"command": ("track", "1")},
            #     ],
            #     "help_text": "Bad command test routine",
            # },
            # "CAP-name": {
            #     "commands": [
            #         {"command": ("track", "0")},
            #         {"command": ("does_not_exist",)},
            #         {"command": ("track", "1")},
            #     ],
            #     "help_text": "Bad command test routine",
            # },
        }
    )
    def test_no_name_given(self):
        self.assertEqual(get_routine("no_name").name, "no_name")
        # self.assertEqual(get_routine("hyphen-name").name, "hyphen-name")
        # self.assertEqual(get_routine("CAP-name").name, "CAP-name")

    @override_settings(
        DJANGO_ROUTINES={
            "bad_command": {
                "commands": [
                    {"command": ("track", "0")},
                    {"comand": ("track", "1")},
                ],
                "help_text": "Bad command test routine",
                "name": "bad_command",
            },
        }
    )
    def test_malformed_command(self):
        with self.assertRaises(ImproperlyConfigured):
            get_command("routine")

    @override_settings(
        DJANGO_ROUTINES={
            "good": {
                "commands": [
                    {"command": ("track", "0")},
                    {"command": ("track", "1")},
                ],
                "help_text": "A good routine",
                "name": "good",
            },
        }
    )
    def test_get_missing_routine(self):
        self.assertEqual(get_routine("good").name, "good")
        with self.assertRaises(KeyError):
            get_routine("dne")

    @override_settings(
        DJANGO_ROUTINES={
            "bad_command": {
                "commands": [
                    {"command": ("track", "0")},
                    {"comand": ("track", "1")},
                ],
                "help_text": "Bad command test routine",
                "name": "bad_command",
            },
        }
    )
    def test_get_malformed_routine(self):
        with self.assertRaises(ImproperlyConfigured):
            get_routine("bad_command")

    # why do these break everything??
    # @override_settings(DJANGO_ROUTINES={})
    # def test_no_routines(self):
    #     with self.assertRaises(CommandError):
    #         call_command("routine")

    # @override_settings(DJANGO_ROUTINES=None)
    # def test_routines_none(self):
    #     with self.assertRaises(CommandError):
    #         call_command("routine")

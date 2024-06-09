from django.test import override_settings, TestCase
from django_routines import ROUTINE_SETTING
from django.conf import settings
from .test_core import CoreTests


@override_settings(
    DJANGO_ROUTINES={
        "bad": {
            "commands": [
                {"command": ("track", "0")},
                {"command": ("does_not_exist",)},
                {"command": ("track", "1")},
            ],
            "help_text": "Bad command test routine",
            "name": "bad",
        },
        "deploy": {
            "commands": [
                {"command": ("makemigrations",), "switches": ["prepare"]},
                {"command": ("migrate",)},
                {"command": ("renderstatic",)},
                {"command": ("collectstatic",)},
                {"command": ("shellcompletion", "install"), "switches": ("initial",)},
                {
                    "command": ("loaddata", "./fixtures/initial_data.json"),
                    "switches": ("demo",),
                },
            ],
            "help_text": "Deploy the site application into production.",
            "name": "deploy",
            "switch_helps": {
                "demo": "Deploy the demo.",
                "prepare": "Prepare the deployment.",
            },
        },
        "test": {
            "commands": [
                {"command": ("track", "2"), "switches": ("initial", "demo")},
                {
                    "command": ("track", "0"),
                    "options": {"verbosity": 0},
                    "priority": 1,
                    "switches": ("initial",),
                },
                {"command": ("track", "3"), "options": {"demo": 2}, "priority": 3},
                {
                    "command": ("track", "4"),
                    "options": {"demo": 6, "flag": True},
                    "priority": 3,
                },
                {"command": ("track", "1"), "priority": 4},
                {"command": ("track", "5"), "priority": 6, "switches": ("demo",)},
            ],
            "help_text": "Test Routine 1",
            "name": "test",
        },
    }
)
class SettingsAsDictTests(CoreTests, TestCase):
    def test_settings_format(self):
        routines = getattr(settings, ROUTINE_SETTING)
        self.assertEqual(
            routines,
            {
                "bad": {
                    "commands": [
                        {"command": ("track", "0")},
                        {"command": ("does_not_exist",)},
                        {"command": ("track", "1")},
                    ],
                    "help_text": "Bad command test routine",
                    "name": "bad",
                },
                "deploy": {
                    "commands": [
                        {"command": ("makemigrations",), "switches": ["prepare"]},
                        {"command": ("migrate",)},
                        {"command": ("renderstatic",)},
                        {"command": ("collectstatic",)},
                        {
                            "command": ("shellcompletion", "install"),
                            "switches": ("initial",),
                        },
                        {
                            "command": ("loaddata", "./fixtures/initial_data.json"),
                            "switches": ("demo",),
                        },
                    ],
                    "help_text": "Deploy the site application into production.",
                    "name": "deploy",
                    "switch_helps": {
                        "demo": "Deploy the demo.",
                        "prepare": "Prepare the deployment.",
                    },
                },
                "test": {
                    "commands": [
                        {"command": ("track", "2"), "switches": ("initial", "demo")},
                        {
                            "command": ("track", "0"),
                            "options": {"verbosity": 0},
                            "priority": 1,
                            "switches": ("initial",),
                        },
                        {
                            "command": ("track", "3"),
                            "options": {"demo": 2},
                            "priority": 3,
                        },
                        {
                            "command": ("track", "4"),
                            "options": {"demo": 6, "flag": True},
                            "priority": 3,
                        },
                        {"command": ("track", "1"), "priority": 4},
                        {
                            "command": ("track", "5"),
                            "priority": 6,
                            "switches": ("demo",),
                        },
                    ],
                    "help_text": "Test Routine 1",
                    "name": "test",
                },
            },
        )

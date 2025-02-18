import os
from django.test import override_settings, TestCase
from django_routines import ROUTINE_SETTING
from django.conf import settings
from pathlib import Path
from .test_core import CoreTests
from . import system_cmd

system_cmd = ("python", str(system_cmd.relative_to(Path(os.getcwd()))))


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
                {"command": "collectstatic", "options": {"interactive": False}},
                {"command": ("shellcompletion", "install"), "switches": ("import",)},
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
        "import": {
            "commands": [
                {"command": ("track", "2"), "switches": ("import", "demo")},
                {
                    "command": ("track", "0"),
                    "options": {"verbosity": 0},
                    "priority": 1,
                    "switches": ("import",),
                },
                {"command": ("track", "3"), "options": {"demo": 2}, "priority": 3},
                {
                    "command": ("track", "4"),
                    "options": {"demo": 6, "flag": True},
                    "priority": 3,
                },
                {"command": ("track", "1"), "priority": 4},
                {"command": ("track", "5"), "priority": 6, "switches": ("demo",)},
                {
                    "command": (*system_cmd, "sys 2"),
                    "priority": 8,
                    "kind": "system",
                },
                {
                    "command": (*system_cmd, "sys 1"),
                    "priority": 7,
                    "kind": "system",
                },
            ],
            "help_text": "Test Routine 1",
            "name": "import",
        },
        "test-hyphen": {
            "commands": [
                {
                    "command": ("track", "1"),
                    "switches": ["--hyphen-ok", "hyphen-ok-prefix"],
                },
                {"command": ("track", "2")},
                {"command": ("track", "3"), "switches": ("hyphen-ok",)},
                {"command": ("track", "4")},
                {
                    "command": ("track", "5"),
                    "switches": ("hyphen-ok", "--hyphen-ok-prefix"),
                },
            ],
            "help_text": "Test that hyphens dont mess everything up.",
            "name": "test-hyphen",
            "switch_helps": {
                "hyphen-ok": "Test hyphen.",
                "--hyphen-ok-prefix": "Test hyphen with -- prefix.",
            },
        },
        "atomic_pass": {
            "name": "atomic_pass",
            "help_text": "Atomic test routine.",
            "commands": [
                {
                    "command": ("edit", "0", "Name1"),
                    "priority": 0,
                    "switches": (),
                    "options": {},
                    "kind": "management",
                },
                {
                    "command": ("edit", "0", "Name2"),
                    "priority": 0,
                    "switches": (),
                    "options": {},
                    "kind": "management",
                },
                {
                    "command": ("edit", "0", "Name3"),
                    "priority": 0,
                    "switches": (),
                    "options": {},
                    "kind": "management",
                },
                {
                    "command": ("edit", "1", "Name4"),
                    "priority": 0,
                    "switches": (),
                    "options": {},
                    "kind": "management",
                },
            ],
            "switch_helps": {},
            "subprocess": False,
            "atomic": True,
            "continue_on_error": False,
        },
        "atomic_fail": {
            "name": "atomic_fail",
            "help_text": "Atomic test routine failure.",
            "commands": [
                {
                    "command": ("edit", "0", "Name1"),
                    "priority": 0,
                    "switches": (),
                    "options": {},
                    "kind": "management",
                },
                {
                    "command": ("edit", "0", "Name2"),
                    "priority": 0,
                    "switches": (),
                    "options": {},
                    "kind": "management",
                },
                {
                    "command": ("edit", "0", "Name3"),
                    "priority": 0,
                    "switches": (),
                    "options": {},
                    "kind": "management",
                },
                {
                    "command": ("edit", "1", "Name4", "--raise"),
                    "priority": 0,
                    "switches": (),
                    "options": {},
                    "kind": "management",
                },
            ],
            "switch_helps": {},
            "subprocess": False,
            "atomic": True,
            "continue_on_error": False,
        },
        "test_continue": {
            "name": "test_continue",
            "help_text": "Test continue option.",
            "commands": [
                {
                    "command": ("edit", "0", "Name1"),
                    "priority": 0,
                    "switches": (),
                    "options": {},
                    "kind": "management",
                },
                {
                    "command": ("edit", "0", "Name2", "--raise"),
                    "priority": 0,
                    "switches": (),
                    "options": {},
                    "kind": "management",
                },
                {
                    "command": ("edit", "0", "Name3"),
                    "priority": 0,
                    "switches": (),
                    "options": {},
                    "kind": "management",
                },
            ],
            "switch_helps": {},
            "subprocess": False,
            "atomic": False,
            "continue_on_error": True,
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
                        {"command": "collectstatic", "options": {"interactive": False}},
                        {
                            "command": ("shellcompletion", "install"),
                            "switches": ("import",),
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
                "import": {
                    "commands": [
                        {"command": ("track", "2"), "switches": ("import", "demo")},
                        {
                            "command": ("track", "0"),
                            "options": {"verbosity": 0},
                            "priority": 1,
                            "switches": ("import",),
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
                        {
                            "command": (*system_cmd, "sys 2"),
                            "priority": 8,
                            "kind": "system",
                        },
                        {
                            "command": (*system_cmd, "sys 1"),
                            "priority": 7,
                            "kind": "system",
                        },
                    ],
                    "help_text": "Test Routine 1",
                    "name": "import",
                },
                "test-hyphen": {
                    "commands": [
                        {
                            "command": ("track", "1"),
                            "switches": ["--hyphen-ok", "hyphen-ok-prefix"],
                        },
                        {"command": ("track", "2")},
                        {"command": ("track", "3"), "switches": ("hyphen-ok",)},
                        {"command": ("track", "4")},
                        {
                            "command": ("track", "5"),
                            "switches": ("hyphen-ok", "--hyphen-ok-prefix"),
                        },
                    ],
                    "help_text": "Test that hyphens dont mess everything up.",
                    "name": "test-hyphen",
                    "switch_helps": {
                        "hyphen-ok": "Test hyphen.",
                        "--hyphen-ok-prefix": "Test hyphen with -- prefix.",
                    },
                },
                "atomic_pass": {
                    "name": "atomic_pass",
                    "help_text": "Atomic test routine.",
                    "commands": [
                        {
                            "command": ("edit", "0", "Name1"),
                            "priority": 0,
                            "switches": (),
                            "options": {},
                            "kind": "management",
                        },
                        {
                            "command": ("edit", "0", "Name2"),
                            "priority": 0,
                            "switches": (),
                            "options": {},
                            "kind": "management",
                        },
                        {
                            "command": ("edit", "0", "Name3"),
                            "priority": 0,
                            "switches": (),
                            "options": {},
                            "kind": "management",
                        },
                        {
                            "command": ("edit", "1", "Name4"),
                            "priority": 0,
                            "switches": (),
                            "options": {},
                            "kind": "management",
                        },
                    ],
                    "switch_helps": {},
                    "subprocess": False,
                    "atomic": True,
                    "continue_on_error": False,
                },
                "atomic_fail": {
                    "name": "atomic_fail",
                    "help_text": "Atomic test routine failure.",
                    "commands": [
                        {
                            "command": ("edit", "0", "Name1"),
                            "priority": 0,
                            "switches": (),
                            "options": {},
                            "kind": "management",
                        },
                        {
                            "command": ("edit", "0", "Name2"),
                            "priority": 0,
                            "switches": (),
                            "options": {},
                            "kind": "management",
                        },
                        {
                            "command": ("edit", "0", "Name3"),
                            "priority": 0,
                            "switches": (),
                            "options": {},
                            "kind": "management",
                        },
                        {
                            "command": ("edit", "1", "Name4", "--raise"),
                            "priority": 0,
                            "switches": (),
                            "options": {},
                            "kind": "management",
                        },
                    ],
                    "switch_helps": {},
                    "subprocess": False,
                    "atomic": True,
                    "continue_on_error": False,
                },
                "test_continue": {
                    "name": "test_continue",
                    "help_text": "Test continue option.",
                    "commands": [
                        {
                            "command": ("edit", "0", "Name1"),
                            "priority": 0,
                            "switches": (),
                            "options": {},
                            "kind": "management",
                        },
                        {
                            "command": ("edit", "0", "Name2", "--raise"),
                            "priority": 0,
                            "switches": (),
                            "options": {},
                            "kind": "management",
                        },
                        {
                            "command": ("edit", "0", "Name3"),
                            "priority": 0,
                            "switches": (),
                            "options": {},
                            "kind": "management",
                        },
                    ],
                    "switch_helps": {},
                    "subprocess": False,
                    "atomic": False,
                    "continue_on_error": True,
                },
            },
        )

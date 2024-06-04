from io import StringIO
from importlib.util import find_spec
import pytest

from django.core.management import BaseCommand, call_command, CommandError
from django_typer import get_command
from django.test import TestCase, override_settings
from django.conf import settings
from django_routines import ROUTINE_SETTING
from django.core.exceptions import ImproperlyConfigured
import re

from tests.django_routines_tests.management.commands.track import (
    invoked,
    passed_options,
)


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
        }
    )
    def test_malformed_routine(self):
        with self.assertRaises(ImproperlyConfigured):
            get_command("routine")

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

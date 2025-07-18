"""
Miscellaneous tests - mostly for coverage
"""

from django_routines import ManagementCommand, SystemCommand


def test_to_dict_return():
    assert isinstance(
        ManagementCommand.from_dict(ManagementCommand("test")), ManagementCommand
    )
    assert isinstance(SystemCommand.from_dict(SystemCommand("test")), SystemCommand)


# def test_key_error():
#     from django.core.management import call_command
#     from django.core.management.base import CommandError

#     try:
#         call_command("keyerr")
#     except CommandError as e:
#         assert "KeyError" in str(e)
#     else:
#         assert False, "CommandError was not raised"


import importlib
from importlib.util import find_spec
import os
from django.test import TestCase, override_settings
from django.core.management import call_command
from django_routines import (
    ROUTINE_SETTING,
    Routine,
    ManagementCommand,
    SystemCommand,
    Command,
)
from . import system_cmd
from pathlib import Path
from functools import partial
import json
from .hooks import pre_hook, post_hook
from tests import track_file

pre_hook_track = partial(pre_hook, label="pre_hook_track")
post_hook_track = partial(post_hook, label="post_hook_track")

system_cmd = ("python", str(system_cmd.relative_to(Path(os.getcwd()))))


DEFAULT_OPTIONS = {
    "force_color": False,
    "no_color": False,
    "skip_checks": True,
    "version": None,
    "verbosity": 1,
    "settings": "",
    "pythonpath": None,
    "traceback": False,
    "subprocess": False,
    "atomic": False,
    "continue_on_error": False,
    "all": False,
}
if find_spec("rich"):
    DEFAULT_OPTIONS["show_locals"] = None


def mult_arg_by_2(command: Command):
    parts = list(command.command)
    command.command = tuple([*parts[:-1], str(int(parts[-1]) * 2)])


def mult_result_by_4(command: Command):
    result = getattr(command.result, "stdout", command.result)
    if result is not None:
        command.result = int(result) * 4


class KeyErrorTest(TestCase):
    """
    https://github.com/bckohan/django-routines/issues/44
    """

    def reload(self):
        from django_routines.management.commands import routine

        importlib.reload(routine)

    @override_settings(
        DJANGO_ROUTINES={
            "keyerr-bug": Routine(
                commands=[
                    ManagementCommand(command=("keyerr",)),
                ],
                help_text=("Test the KeyError exception bug."),
                name="keyerr-bug",
            ),
        }
    )
    def test_key_err(self):
        self.reload()
        with self.assertRaises(KeyError):
            call_command("routine", "keyerr-bug")

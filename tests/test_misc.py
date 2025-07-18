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


@override_settings(DJANGO_ROUTINES={})
def test_command_spec():
    import os
    from pathlib import Path
    from django_routines import (
        routine,
        command,
        system,
        ManagementCommand,
        _RoutineCommand,
        SystemCommand,
        Routine,
        routines,
        get_routine,
    )
    from tests import system_cmd

    system_cmd = ("python", str(system_cmd.relative_to(Path(os.getcwd()))))

    command("import", "track", "2", priority=0, switches=("import", "demo"))
    routine(
        "import",
        "Test Routine 1",
        ManagementCommand(
            ("track", "0"), priority=1, switches=("import",), options={"verbosity": 0}
        ),
        ManagementCommand(("track", "1"), priority=4),
        SystemCommand((*system_cmd, "sys 2"), priority=8),
    )

    command("import", "track", "3", priority=3, demo=2)
    command("import", "track", "4", priority=3, demo=6, flag=True)
    command("import", "track", "5", priority=6, switches=["demo"])
    system("import", *system_cmd, "sys 1", priority=7)

    import_routine = globals()["DJANGO_ROUTINES"]["import"]
    assert import_routine["commands"][-1].get("system")[0] == "python"
    assert import_routine["commands"][-2].get("system")[0] == "python"

    assert "system" in import_routine["commands"][-1]
    assert "system" in import_routine["commands"][-2]

    _RoutineCommand.from_dict(import_routine["commands"][-1])
    assert "system" in import_routine["commands"][-2]
    assert "system" in import_routine["commands"][-1]

    import_routine = get_routine("import", scope=globals())

    assert import_routine.name == "import"
    assert import_routine.commands[-1].command[0] == "python"
    assert isinstance(import_routine.commands[-1], SystemCommand)
    assert import_routine.commands[-2].command[0] == "python"
    assert isinstance(import_routine.commands[-2], SystemCommand)

    import_routine = globals()["DJANGO_ROUTINES"]["import"]
    assert "system" in import_routine["commands"][-1]
    assert "system" in import_routine["commands"][-2]
    assert "command" not in import_routine["commands"][-1]
    assert "command" not in import_routine["commands"][-2]

    import_routine = list(routines(scope=globals()))[0]
    assert import_routine.name == "import"
    assert import_routine.commands[0].management[0] == "track"
    assert import_routine.commands[-1].command[0] == "python"
    assert isinstance(import_routine.commands[-1], SystemCommand)
    assert import_routine.commands[-2].command[0] == "python"
    assert isinstance(import_routine.commands[-2], SystemCommand)
    assert import_routine.commands[-2].system[0] == "python"


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

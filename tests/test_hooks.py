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

post_hook_ret = partial(post_hook, ret=True)
pre_hook_override = partial(pre_hook, label="pre_hook_override")

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


class HooksTests(TestCase):
    def setUp(self):
        if track_file.is_file():
            os.remove(track_file)
        self.reload()
        super().setUp()

    def tearDown(self):
        if track_file.is_file():
            os.remove(track_file)
        super().setUp()

    def reload(self):
        from django_routines.management.commands import routine

        importlib.reload(routine)

    @override_settings(
        DJANGO_ROUTINES={
            "routine-hooks": Routine(
                commands=[
                    ManagementCommand(command=("track", "0"), switches=["switch"]),
                    ManagementCommand(command=("track", "1")),
                    ManagementCommand(
                        command=("track", "2"),
                        post_hook=partial(post_hook, label="post_hook_override"),
                    ),
                    SystemCommand(
                        command=(*system_cmd, "track 3"),
                        pre_hook="tests.test_hooks.pre_hook_override",
                    ),
                ],
                help_text=(
                    "Test pre/post hooks at the routine and command level overrides."
                ),
                pre_hook="tests.test_hooks.pre_hook_track",
                post_hook="tests.test_hooks.post_hook_track",
                name="routine-hooks",
                continue_on_error=True,
            ),
        }
    )
    def test_routine_hooks(self):
        self.reload()
        call_command("routine", "--no-color", "routine-hooks", "--switch")
        track = json.loads(track_file.read_text())
        self.assertEqual(track["invoked"], [0, 1, 2, "track 3"])
        self.assertEqual(len(track["pre_hooks"]), 4)
        self.assertEqual(len(track["post_hooks"]), 4)
        self.assertEqual(track["pre_hooks"][0][0], "pre_hook_track")
        self.assertEqual(track["post_hooks"][0][0], "post_hook_track")
        self.assertEqual(track["pre_hooks"][1][0], "pre_hook_track")
        self.assertEqual(track["post_hooks"][1][0], "post_hook_track")
        self.assertEqual(track["pre_hooks"][2][0], "pre_hook_track")
        self.assertEqual(track["post_hooks"][2][0], "post_hook_override")
        self.assertEqual(track["pre_hooks"][3][0], "pre_hook_override")
        self.assertEqual(track["post_hooks"][3][0], "post_hook_track")

        for idx, (pre, post) in enumerate(zip(track["pre_hooks"], track["post_hooks"])):
            self.assertEqual(pre[1], "routine_hooks")
            self.assertEqual(post[1], "routine_hooks")
            self.assertTrue(pre[2].endswith(f"track {idx}"))
            self.assertTrue(post[2].endswith(f"track {idx}"))
            if idx == 0:
                self.assertIsNone(pre[3])
                self.assertEqual(post[3], f"track {idx + 1}")
            elif idx == 3:
                self.assertTrue(pre[3].endswith(f"track {idx - 1}"))
                self.assertIsNone(post[3])
            else:
                self.assertTrue(pre[3].endswith(f"track {idx - 1}"))
                self.assertTrue(post[3].endswith(f"track {idx + 1}"))

            expected = {
                **DEFAULT_OPTIONS,
                "continue_on_error": True,
                "no_color": True,
                "switch": True,
            }
            pre_opts = pre[4]
            post_opts = post[4]
            del pre_opts["manage_script"]
            del post_opts["manage_script"]
            self.assertDictEqual(pre_opts, expected)
            self.assertDictEqual(post_opts, expected)

    @override_settings(
        DJANGO_ROUTINES={
            "routine-hooks": Routine(
                commands=[
                    ManagementCommand(command=("track", "0")),
                    ManagementCommand(command=("track", "1")),
                    ManagementCommand(
                        command=("track", "2"),
                        post_hook="tests.test_hooks.post_hook_ret",
                    ),
                    ManagementCommand(command=("track", "3")),
                ],
                help_text=("Test routine halt for management commands via post-hooks."),
                name="routine-hooks",
            ),
        }
    )
    def test_halt_routine1(self):
        self.reload()
        call_command("routine", "routine-hooks")
        track = json.loads(track_file.read_text())
        self.assertEqual(len(track.get("pre_hooks", [])), 0)
        self.assertEqual(len(track.get("post_hooks", [])), 1)
        self.assertEqual(track["invoked"], [0, 1, 2])

    @override_settings(
        DJANGO_ROUTINES={
            "routine-hooks": Routine(
                commands=[
                    ManagementCommand(command=("track", "0")),
                    ManagementCommand(command=("track", "1")),
                    SystemCommand(
                        command=(*system_cmd, "track 2"),
                        post_hook=partial(post_hook, ret=True),
                    ),
                    ManagementCommand(command=("track", "3")),
                ],
                help_text=("Test routine halt for system commands via post-hooks."),
                name="routine-hooks",
            ),
        }
    )
    def test_halt_routine2(self):
        self.reload()
        call_command("routine", "routine-hooks")
        track = json.loads(track_file.read_text())
        self.assertEqual(len(track.get("pre_hooks", [])), 0)
        self.assertEqual(len(track.get("post_hooks", [])), 1)
        self.assertEqual(track["invoked"], [0, 1, "track 2"])

    @override_settings(
        DJANGO_ROUTINES={
            "routine-hooks": Routine(
                commands=[
                    ManagementCommand(command=("track", "0"), pre_hook=pre_hook),
                    ManagementCommand(
                        command=("track", "1"), pre_hook=partial(pre_hook, ret=True)
                    ),
                    SystemCommand(
                        command=(*system_cmd, "track 2"),
                        pre_hook=partial(pre_hook, ret=True),
                    ),
                    ManagementCommand(command=("track", "3"), pre_hook=pre_hook),
                    ManagementCommand(command=("track", "4"), pre_hook=pre_hook),
                ],
                help_text=("Test command skipping via pre-hooks."),
                name="routine-hooks",
            ),
        }
    )
    def test_skip_commands(self):
        self.reload()
        call_command("routine", "routine-hooks")
        track = json.loads(track_file.read_text())
        pre_hooks = track["pre_hooks"]
        self.assertEqual(len(pre_hooks), 5)
        self.assertEqual(len(track.get("post_hooks", [])), 0)
        for idx, pre in enumerate(pre_hooks):
            self.assertEqual(pre[0], "track")
            self.assertEqual(pre[1], "routine_hooks")
            self.assertTrue(pre[2].endswith(f"track {idx}"))
        self.assertIsNone(pre_hooks[0][3])
        self.assertEqual(pre_hooks[1][3], "track 0")
        self.assertEqual(pre_hooks[2][3], "track 0")
        self.assertEqual(pre_hooks[3][3], "track 0")
        self.assertEqual(pre_hooks[4][3], "track 3")
        self.assertEqual(track["invoked"], [0, 3, 4])

    @override_settings(
        DJANGO_ROUTINES={
            "routine-hooks": Routine(
                commands=[
                    ManagementCommand(command=("rtrack", "0"), post_hook=post_hook),
                    ManagementCommand(
                        command=("rtrack", "1"),
                        pre_hook=partial(pre_hook, modify=mult_arg_by_2),
                        post_hook=partial(post_hook, modify=mult_result_by_4),
                    ),
                    SystemCommand(
                        command=(*system_cmd, "rtrack", "2"),
                        pre_hook=partial(pre_hook, modify=mult_arg_by_2),
                        post_hook=partial(post_hook, modify=mult_result_by_4),
                    ),
                    ManagementCommand(
                        command=("rtrack", "3"), pre_hook=partial(pre_hook)
                    ),
                ],
                help_text=("Test command modification in hooks."),
                name="routine-hooks",
            ),
        }
    )
    def test_hook_command_mutability(self):
        self.reload()
        call_command("routine", "routine-hooks")
        track = json.loads(track_file.read_text())
        pre_hooks = track.get("pre_hooks", [])
        post_hooks = track.get("post_hooks", [])
        self.assertEqual(len(pre_hooks), 3)
        self.assertEqual(len(post_hooks), 3)
        self.assertEqual(track["invoked"][0], 0)
        self.assertEqual(track["invoked"][1], 2)
        self.assertEqual(track["invoked"][2], "4")
        self.assertEqual(track["invoked"][3], 3)
        self.assertEqual(post_hooks[0][5], "0")
        self.assertEqual(pre_hooks[0][6], "0")
        self.assertEqual(post_hooks[1][5], "2")
        self.assertEqual(pre_hooks[1][6], 8)
        # TODO - https://github.com/bckohan/django-routines/issues/41
        # self.assertEqual(post_hooks[2][5], 16)
        # self.assertEqual(pre_hooks[2][6], 16)

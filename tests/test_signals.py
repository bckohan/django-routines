"""
Miscellaneous tests - mostly for coverage
"""

import typing as t
from django.core.management import call_command, CommandError
from django.test import TestCase, override_settings
from django_routines import Routine, ManagementCommand, SystemCommand
from functools import partial
from django_routines.signals import routine_started, routine_finished, routine_failed
from django_routines.exceptions import ExitEarly
from collections import namedtuple
from pathlib import Path
import importlib
from .hooks import pre_hook, post_hook
from . import system_cmd
import os


system_cmd = ("python", str(system_cmd.relative_to(Path(os.getcwd()))))


Started = namedtuple("Started", ["sender", "routine", "signal", "kwargs"])
Finished = namedtuple(
    "Finished", ["sender", "routine", "early_exit", "last_command", "signal", "kwargs"]
)
Failed = namedtuple(
    "Failed", ["sender", "routine", "failed_command", "exception", "signal", "kwargs"]
)


class TestSignals(TestCase):
    routine_started_log: t.List[Started] = []
    routine_finished_log: t.List[Finished] = []
    routine_failed_log: t.List[Failed] = []

    # failed signal behavior toggles
    do_exit_early = False
    do_continue = False

    subprocess = False

    def reload(self):
        from django_routines.management.commands import routine

        importlib.reload(routine)

    def setUp(self):
        self.routine_started_log.clear()
        self.routine_finished_log.clear()
        self.routine_failed_log.clear()
        routine_started.connect(self.routine_started)
        routine_finished.connect(self.routine_finished)
        routine_failed.connect(self.routine_failed)
        self.do_exit_early = False
        self.do_continue = False
        super().setUp()

    def tearDown(self):
        super().tearDown()
        routine_started.disconnect(self.routine_started)
        routine_finished.disconnect(self.routine_finished)
        routine_failed.disconnect(self.routine_failed)
        self.routine_started_log.clear()
        self.routine_finished_log.clear()
        self.routine_failed_log.clear()
        self.do_exit_early = False
        self.do_continue = False

    def routine_started(self, sender, routine, signal, **kwargs):
        self.routine_started_log.append(Started(sender, routine, signal, kwargs))

    def routine_finished(
        self, sender, routine, early_exit, last_command, signal, **kwargs
    ):
        self.routine_finished_log.append(
            Finished(sender, routine, early_exit, last_command, signal, kwargs)
        )

    def routine_failed(
        self, sender, routine, failed_command, exception, signal, **kwargs
    ):
        self.routine_failed_log.append(
            Failed(sender, routine, failed_command, exception, signal, kwargs)
        )
        if self.do_exit_early:
            raise ExitEarly("Exiting early due to signal.")
        if self.do_continue:
            return True

    def call_command(self, *args, **kwargs):
        if self.subprocess:
            kwargs["subprocess"] = True
            kwargs["manage_script"] = "./manage.py"
        call_command(*args, **kwargs)

    def test_signals_nominal(self):
        self.reload()
        from django_routines.management.commands.routine import (
            Command as RoutineCommand,
        )

        self.call_command("routine", "deploy", "--prepare")
        self.assertEqual(len(self.routine_started_log), 1)
        self.assertEqual(len(self.routine_finished_log), 1)
        self.assertEqual(len(self.routine_failed_log), 0)
        self.assertIsInstance(self.routine_started_log[0].sender, RoutineCommand)
        self.assertIsInstance(self.routine_finished_log[0].sender, RoutineCommand)
        self.assertIs(
            self.routine_started_log[0].sender, self.routine_finished_log[0].sender
        )
        cmd: RoutineCommand = self.routine_started_log[0].sender

        self.assertEqual(self.routine_started_log[0].routine, "deploy")
        self.assertEqual(self.routine_finished_log[0].routine, "deploy")
        self.assertEqual(self.routine_finished_log[0].early_exit, False)
        self.assertEqual(self.routine_finished_log[0].last_command, 3)
        self.assertEqual(
            cmd.plan[self.routine_finished_log[0].last_command].command_name,
            "collectstatic",
        )
        self.assertTrue(self.routine_started_log[0].kwargs.get("prepare", None))
        if self.subprocess:
            self.assertTrue(self.routine_started_log[0].kwargs.get("subprocess", None))
        else:
            self.assertTrue(
                self.routine_started_log[0].kwargs.get("subprocess", None) is False
            )
        self.assertTrue(self.routine_started_log[0].kwargs.get("all", None) is False)
        self.assertTrue(self.routine_started_log[0].kwargs.get("atomic", None) is False)
        self.assertTrue(
            self.routine_started_log[0].kwargs.get("continue_on_error", None) is False
        )
        self.assertTrue(self.routine_started_log[0].kwargs.get("demo", None) is False)
        self.assertTrue(
            self.routine_started_log[0].kwargs.get("force_color", None) is False
        )
        self.assertTrue(
            self.routine_started_log[0].kwargs.get("no_color", None) is False
        )
        self.assertTrue(
            self.routine_started_log[0].kwargs.get("traceback", None) is False
        )
        self.assertEqual(self.routine_started_log[0].kwargs.get("verbosity", None), 1)
        self.assertDictEqual(
            self.routine_finished_log[0].kwargs, self.routine_started_log[0].kwargs
        )

    @override_settings(
        DJANGO_ROUTINES={
            "routine-hooks": Routine(
                commands=[
                    ManagementCommand(command=("track", "0")),
                    ManagementCommand(
                        command=("track", "1"), post_hook=partial(post_hook, ret=True)
                    ),
                    SystemCommand(
                        command=(*system_cmd, "track 2"),
                    ),
                    ManagementCommand(command=("track", "3")),
                ],
                help_text=(
                    "Test signals issued when command is skipped and early exit triggered."
                ),
                name="routine-hooks",
            ),
        }
    )
    def test_signal_early_exit1(self):
        self.reload()
        self.call_command("routine", "routine-hooks")
        self.assertEqual(len(self.routine_started_log), 1)
        self.assertEqual(len(self.routine_finished_log), 1)
        self.assertEqual(len(self.routine_failed_log), 0)
        self.assertEqual(self.routine_started_log[0].routine, "routine_hooks")
        self.assertEqual(self.routine_finished_log[0].routine, "routine_hooks")
        self.assertEqual(self.routine_finished_log[0].early_exit, True)
        self.assertEqual(self.routine_finished_log[0].last_command, 1)

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
                help_text=(
                    "Test signals issued when command is skipped and early exit triggered."
                ),
                name="routine-hooks",
            ),
        }
    )
    def test_signal_early_exit(self):
        self.reload()
        self.call_command("routine", "routine-hooks")
        self.assertEqual(len(self.routine_started_log), 1)
        self.assertEqual(len(self.routine_finished_log), 1)
        self.assertEqual(len(self.routine_failed_log), 0)
        self.assertEqual(self.routine_started_log[0].routine, "routine_hooks")
        self.assertEqual(self.routine_finished_log[0].routine, "routine_hooks")
        self.assertEqual(self.routine_finished_log[0].early_exit, True)
        self.assertEqual(self.routine_finished_log[0].last_command, 2)

    @override_settings(
        DJANGO_ROUTINES={
            "routine-hooks": Routine(
                commands=[
                    ManagementCommand(command=("track", "0")),
                    ManagementCommand(command=("track", "1")),
                    SystemCommand(
                        command=(*system_cmd, "track 2"),
                        pre_hook=partial(pre_hook, ret=True),
                    ),
                    ManagementCommand(
                        command=("track", "3"), pre_hook=partial(pre_hook, ret=True)
                    ),
                ],
                help_text=(
                    "Test that last_command holds the correct value based on skips."
                ),
                name="routine-hooks",
            ),
        }
    )
    def test_signal_last_command(self):
        self.reload()
        self.call_command("routine", "routine-hooks")
        self.assertEqual(len(self.routine_started_log), 1)
        self.assertEqual(len(self.routine_finished_log), 1)
        self.assertEqual(len(self.routine_failed_log), 0)
        self.assertEqual(self.routine_started_log[0].routine, "routine_hooks")
        self.assertEqual(self.routine_finished_log[0].routine, "routine_hooks")
        self.assertEqual(self.routine_finished_log[0].early_exit, False)
        self.assertEqual(self.routine_finished_log[0].last_command, 1)

    @override_settings(
        DJANGO_ROUTINES={
            "routine-hooks": Routine(
                commands=[
                    ManagementCommand(command=("track", "0")),
                    ManagementCommand(command=("track", "1")),
                    SystemCommand(command=(*system_cmd, "track 2")),
                    ManagementCommand(command=("track", "3")),
                ],
                help_text=("Test that last_command holds the correct value."),
                name="routine-hooks",
            ),
        }
    )
    def test_signal_last_command_nominal(self):
        self.reload()
        self.call_command("routine", "routine-hooks")
        self.assertEqual(len(self.routine_started_log), 1)
        self.assertEqual(len(self.routine_finished_log), 1)
        self.assertEqual(len(self.routine_failed_log), 0)
        self.assertEqual(self.routine_started_log[0].routine, "routine_hooks")
        self.assertEqual(self.routine_finished_log[0].routine, "routine_hooks")
        self.assertEqual(self.routine_finished_log[0].early_exit, False)
        self.assertEqual(self.routine_finished_log[0].last_command, 3)

    @override_settings(
        DJANGO_ROUTINES={
            "routine-hooks": Routine(
                commands=[
                    ManagementCommand(
                        command=("track", "0"), pre_hook=partial(pre_hook, ret=True)
                    ),
                    ManagementCommand(
                        command=("track", "1"), pre_hook=partial(pre_hook, ret=True)
                    ),
                    SystemCommand(
                        command=(*system_cmd, "track 2"),
                        pre_hook=partial(pre_hook, ret=True),
                    ),
                    ManagementCommand(
                        command=("track", "3"), pre_hook=partial(pre_hook, ret=True)
                    ),
                ],
                help_text=("Test last_command is None if all commands are skipped."),
                name="routine-hooks",
            ),
        }
    )
    def test_signal_last_command_skipped_all(self):
        self.reload()
        self.call_command("routine", "routine-hooks")
        self.assertEqual(len(self.routine_started_log), 1)
        self.assertEqual(len(self.routine_finished_log), 1)
        self.assertEqual(len(self.routine_failed_log), 0)
        self.assertEqual(self.routine_started_log[0].routine, "routine_hooks")
        self.assertEqual(self.routine_finished_log[0].routine, "routine_hooks")
        self.assertEqual(self.routine_finished_log[0].early_exit, False)
        self.assertEqual(self.routine_finished_log[0].last_command, None)

    @override_settings(
        DJANGO_ROUTINES={
            "routine-hooks": Routine(
                commands=[
                    ManagementCommand(command=("track", "0")),
                    ManagementCommand(command=("track", "1", "--raise")),
                    ManagementCommand(command=("track", "3")),
                ],
                help_text=(
                    "Test signals issued when command is skipped and early exit triggered."
                ),
                name="routine-hooks",
            ),
        }
    )
    def test_signal_failed(self):
        self.reload()
        from .django_routines_tests.management.commands.track import TestError

        try:
            self.call_command("routine", "routine-hooks")
        except (CommandError, TestError):
            self.assertEqual(len(self.routine_started_log), 1)
            self.assertEqual(len(self.routine_finished_log), 0)
            self.assertEqual(len(self.routine_failed_log), 1)
            self.assertEqual(self.routine_started_log[0].routine, "routine_hooks")
            self.assertEqual(self.routine_failed_log[0].routine, "routine_hooks")
            self.assertIsInstance(
                self.routine_failed_log[0].exception,
                CommandError if self.subprocess else TestError,
            )
            self.assertEqual(self.routine_failed_log[0].failed_command, 1)

    @override_settings(
        DJANGO_ROUTINES={
            "routine-hooks": Routine(
                commands=[
                    ManagementCommand(command=("track", "0")),
                    ManagementCommand(command=("track", "1", "--raise")),
                    ManagementCommand(command=("track", "3")),
                ],
                help_text=(
                    "Test signals issued when command is skipped and early exit triggered."
                ),
                name="routine-hooks",
            ),
        }
    )
    def test_signal_failed_exit_early(self):
        self.reload()
        from .django_routines_tests.management.commands.track import TestError

        self.do_exit_early = True
        self.call_command("routine", "routine-hooks")
        self.assertEqual(len(self.routine_started_log), 1)
        self.assertEqual(len(self.routine_finished_log), 1)
        self.assertEqual(len(self.routine_failed_log), 1)
        self.assertEqual(self.routine_started_log[0].routine, "routine_hooks")
        self.assertEqual(self.routine_failed_log[0].routine, "routine_hooks")
        self.assertIsInstance(
            self.routine_failed_log[0].exception,
            CommandError if self.subprocess else TestError,
        )
        self.assertEqual(self.routine_failed_log[0].failed_command, 1)
        self.assertEqual(self.routine_finished_log[0].last_command, 1)
        self.do_exit_early = False

    @override_settings(
        DJANGO_ROUTINES={
            "routine-hooks": Routine(
                commands=[
                    ManagementCommand(command=("track", "0")),
                    ManagementCommand(command=("track", "1", "--raise")),
                    ManagementCommand(command=("track", "3")),
                ],
                help_text=(
                    "Test signals issued when command is skipped and early exit triggered."
                ),
                name="routine-hooks",
            ),
        }
    )
    def test_signal_failed_continue(self):
        self.reload()
        from .django_routines_tests.management.commands.track import TestError

        self.do_continue = True
        self.call_command("routine", "routine-hooks")
        self.assertEqual(len(self.routine_started_log), 1)
        self.assertEqual(len(self.routine_finished_log), 1)
        self.assertEqual(len(self.routine_failed_log), 1)
        self.assertEqual(self.routine_started_log[0].routine, "routine_hooks")
        self.assertEqual(self.routine_failed_log[0].routine, "routine_hooks")
        self.assertIsInstance(
            self.routine_failed_log[0].exception,
            CommandError if self.subprocess else TestError,
        )
        self.assertEqual(self.routine_failed_log[0].failed_command, 1)
        self.assertEqual(self.routine_finished_log[0].last_command, 2)
        self.do_continue = False


class TestSignalsSubprocess(TestSignals):
    """
    Test signals in a subprocess to ensure they are correctly handled.
    """

    subprocess = True

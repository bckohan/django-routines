from io import StringIO
from importlib.util import find_spec
import pytest

from django.core.management import BaseCommand, call_command, CommandError
from django_typer import get_command
from django.test import TestCase, override_settings
from django.conf import settings
from django_routines import ROUTINE_SETTING, Routine, RoutineCommand
import re

from tests.django_routines_tests.management.commands.track import (
    invoked,
    passed_options,
)


class Tests(TestCase):
    def strip_ansi(self, text):
        ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
        return ansi_escape.sub("", text)

    def lines(self, text, no_color):
        if no_color:
            self.assertTrue("\x1b" not in text)
        else:
            self.assertTrue("\x1b" in text)
        return self.strip_ansi(text).strip().splitlines()

    def test_command(self, no_color=True, verbosity=None):
        invoked.clear()
        passed_options.clear()

        command = (
            "routine",
            ("--no-color" if no_color else "--force-color"),
            *(("--verbosity", str(verbosity)) if verbosity is not None else tuple()),
            "test",
        )
        out = StringIO()
        call_command(*command, stdout=out)
        expected = [3, 4, 1]
        if verbosity is None or verbosity > 0:
            self.assertEqual(
                self.lines(out.getvalue(), no_color=no_color),
                [f"track {id}" for id in expected],
            )
        else:
            self.assertFalse(out.getvalue().strip())
        self.assertEqual(invoked, expected)
        self.assertEqual(passed_options[0]["demo"], 2)
        self.assertEqual(passed_options[1]["demo"], 6)
        if verbosity is not None:
            for idx, opts in enumerate(passed_options):
                self.assertEqual(opts["verbosity"], verbosity)
        invoked.clear()
        passed_options.clear()

        out = StringIO()
        call_command(*command, "--all", stdout=out)
        expected = [2, 0, 3, 4, 1, 5]
        if verbosity is None or verbosity > 0:
            self.assertEqual(
                self.lines(out.getvalue(), no_color=no_color),
                [f"track {id}" for id in expected],
            )
        else:
            self.assertFalse(out.getvalue().strip())
        self.assertEqual(invoked, expected)
        self.assertEqual(passed_options[1]["verbosity"], 0)
        self.assertEqual(passed_options[2]["demo"], 2)
        self.assertEqual(passed_options[3]["demo"], 6)
        if verbosity is not None:
            for idx, opts in enumerate(passed_options):
                if idx != 1:
                    self.assertEqual(opts["verbosity"], verbosity)
        invoked.clear()
        passed_options.clear()

        out = StringIO()
        call_command(*command, "--demo", stdout=out)
        expected = [2, 3, 4, 1, 5]
        if verbosity is None or verbosity > 0:
            self.assertEqual(
                self.lines(out.getvalue(), no_color=no_color),
                [f"track {id}" for id in expected],
            )
        else:
            self.assertFalse(out.getvalue().strip())
        self.assertEqual(invoked, expected)
        self.assertEqual(passed_options[1]["demo"], 2)
        self.assertEqual(passed_options[2]["demo"], 6)
        if verbosity is not None:
            for idx, opts in enumerate(passed_options):
                self.assertEqual(opts["verbosity"], verbosity)
        invoked.clear()
        passed_options.clear()

        out = StringIO()
        call_command(*command, "--demo", "--initial", stdout=out)
        expected = [2, 0, 3, 4, 1, 5]
        if verbosity is None or verbosity > 0:
            self.assertEqual(
                self.lines(out.getvalue(), no_color=no_color),
                [f"track {id}" for id in expected],
            )
        else:
            self.assertFalse(out.getvalue().strip())
        self.assertEqual(invoked, expected)
        self.assertEqual(passed_options[1]["verbosity"], 0)
        self.assertEqual(passed_options[2]["demo"], 2)
        self.assertEqual(passed_options[3]["demo"], 6)
        if verbosity is not None:
            for idx, opts in enumerate(passed_options):
                if idx != 1:
                    self.assertEqual(opts["verbosity"], verbosity)
        invoked.clear()
        passed_options.clear()

        out = StringIO()
        call_command(*command, "--initial", stdout=out)
        expected = [2, 0, 3, 4, 1]
        if verbosity is None or verbosity > 0:
            self.assertEqual(
                self.lines(out.getvalue(), no_color=no_color),
                [f"track {id}" for id in expected],
            )
        else:
            self.assertFalse(out.getvalue().strip())
        self.assertEqual(invoked, expected)
        self.assertEqual(passed_options[1]["verbosity"], 0)
        self.assertEqual(passed_options[2]["demo"], 2)
        self.assertEqual(passed_options[3]["demo"], 6)
        if verbosity is not None:
            for idx, opts in enumerate(passed_options):
                if idx != 1:
                    self.assertEqual(opts["verbosity"], verbosity)
        invoked.clear()
        passed_options.clear()

    def test_command_color(self):
        self.test_command(no_color=False)

    def test_verbosity(self):
        self.test_command(verbosity=3)
        self.test_command(verbosity=0)
        self.test_command(verbosity=2)
        self.test_command(verbosity=1)

    def test_list(self, no_color=True):
        if no_color:
            command = ("routine", "--no-color", "test")
        else:
            command = ("routine", "--force-color", "test")

        out = StringIO()
        call_command(*command, "--all", "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[0] track 2 | initial, demo",
                "[1] track 0 (verbosity=0) | initial",
                "[3] track 3 (demo=2)",
                "[3] track 4 (demo=6)",
                "[4] track 1",
                "[6] track 5 | demo",
            ],
        )

        out = StringIO()
        call_command(*command, "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan, ["[3] track 3 (demo=2)", "[3] track 4 (demo=6)", "[4] track 1"]
        )

        out = StringIO()
        call_command(*command, "--demo", "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[0] track 2 | initial, demo",
                "[3] track 3 (demo=2)",
                "[3] track 4 (demo=6)",
                "[4] track 1",
                "[6] track 5 | demo",
            ],
        )

        out = StringIO()
        call_command(*command, "--demo", "--initial", "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[0] track 2 | initial, demo",
                "[1] track 0 (verbosity=0) | initial",
                "[3] track 3 (demo=2)",
                "[3] track 4 (demo=6)",
                "[4] track 1",
                "[6] track 5 | demo",
            ],
        )

        out = StringIO()
        call_command(*command, "--initial", "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[0] track 2 | initial, demo",
                "[1] track 0 (verbosity=0) | initial",
                "[3] track 3 (demo=2)",
                "[3] track 4 (demo=6)",
                "[4] track 1",
            ],
        )

    def test_list_color(self):
        self.test_list(no_color=False)

    def test_routine_with_bad_command(self):
        with self.assertRaises(CommandError):
            call_command("routine", "bad")

    routine_help_rich = """
 Usage: ./manage.py routine [OPTIONS] COMMAND [ARGS]...                         
                                                                                
 Run batches of commands configured in settings.                                
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --help          Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Django ─────────────────────────────────────────────────────────────────────╮
│ --verbosity          INTEGER RANGE [0<=x<=3]  Verbosity level; 0=minimal     │
│                                               output, 1=normal output,       │
│                                               2=verbose output, 3=very       │
│                                               verbose output                 │
│                                               [default: 1]                   │
│ --version                                     Show program's version number  │
│                                               and exit.                      │
│ --settings           TEXT                     The Python path to a settings  │
│                                               module, e.g.                   │
│                                               "myproject.settings.main". If  │
│                                               this isn't provided, the       │
│                                               DJANGO_SETTINGS_MODULE         │
│                                               environment variable will be   │
│                                               used.                          │
│ --pythonpath         PATH                     A directory to add to the      │
│                                               Python path, e.g.              │
│                                               "/home/djangoprojects/myproje… │
│                                               [default: None]                │
│ --traceback                                   Raise on CommandError          │
│                                               exceptions                     │
│ --no-color                                    Don't colorize the command     │
│                                               output.                        │
│ --force-color                                 Force colorization of the      │
│                                               command output.                │
│ --skip-checks                                 Skip system checks.            │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ bad      Bad command test routine                                            │
│ deploy   Deploy the site application into production.                        │
│ test     Test Routine 1                                                      │
╰──────────────────────────────────────────────────────────────────────────────╯
"""

    routine_test_help_rich = """
 Usage: ./manage.py routine test [OPTIONS] COMMAND [ARGS]...                    
                                                                                
                                                                                
 Test Routine 1                                                                 
                                                                                
                                                                                
 [0] track 2 | initial, demo                                                    
 [1] track 0 (verbosity=0) | initial                                            
 [3] track 3 (demo=2)                                                           
 [3] track 4 (demo=6)                                                           
 [4] track 1                                                                    
 [6] track 5 | demo                                                             
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --all              Include all switched commands.                            │
│ --demo                                                                       │
│ --initial                                                                    │
│ --help             Show this message and exit.                               │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ list   List the commands that will be run.                                   │
╰──────────────────────────────────────────────────────────────────────────────╯
"""

    @pytest.mark.skipif(find_spec("rich") is None, reason="Rich is not installed.")
    def test_helps_rich(self):
        stdout = StringIO()
        routine = get_command("routine", BaseCommand, stdout=stdout, no_color=True)
        routine.print_help("./manage.py", "routine")
        self.assertEqual(stdout.getvalue().strip(), self.routine_help_rich.strip())
        stdout.truncate(0)
        stdout.seek(0)

        routine.print_help("./manage.py", "routine", "test")
        self.assertEqual(
            stdout.getvalue().strip().replace("\x08", ""),
            self.routine_test_help_rich.strip(),
        )

    routine_help_no_rich = """
Usage: ./manage.py routine [OPTIONS] COMMAND [ARGS]...

  Run batches of commands configured in settings.

Options:
  --verbosity INTEGER RANGE  Verbosity level; 0=minimal output, 1=normal
                             output, 2=verbose output, 3=very verbose output
                             [default: 1; 0<=x<=3]
  --version                  Show program's version number and exit.
  --settings TEXT            The Python path to a settings module, e.g.
                             "myproject.settings.main". If this isn't
                             provided, the DJANGO_SETTINGS_MODULE environment
                             variable will be used.
  --pythonpath PATH          A directory to add to the Python path, e.g.
                             "/home/djangoprojects/myproject".
  --traceback                Raise on CommandError exceptions
  --no-color                 Don't colorize the command output.
  --force-color              Force colorization of the command output.
  --skip-checks              Skip system checks.
  --help                     Show this message and exit.

Commands:
  bad     Bad command test routine
  deploy  Deploy the site application into production.
  test    Test Routine 1
"""

    routine_test_help_no_rich = """
Usage: ./manage.py routine test [OPTIONS] COMMAND [ARGS]...

  Test Routine 1
  -----------------------------------
  
  [0] track 2 | initial, demo
  [1] track 0 (verbosity=0) | initial
  [3] track 3 (demo=2)
  [3] track 4 (demo=6)
  [4] track 1
  [6] track 5 | demo

Options:
  --all      Include all switched commands.
  --demo
  --initial
  --help     Show this message and exit.

Commands:
  list  List the commands that will be run.
"""

    @pytest.mark.skipif(find_spec("rich") is not None, reason="Rich is installed.")
    def test_helps_no_rich(self):
        stdout = StringIO()
        routine = get_command("routine", BaseCommand, stdout=stdout, no_color=True)
        routine.print_help("./manage.py", "routine")
        self.assertEqual(stdout.getvalue().strip(), self.routine_help_no_rich.strip())
        stdout.truncate(0)
        stdout.seek(0)

        routine.print_help("./manage.py", "routine", "test")
        self.assertEqual(
            stdout.getvalue().strip().replace("\x08", ""),
            self.routine_test_help_no_rich.strip(),
        )

    def test_settings_format(self):
        routines = getattr(settings, ROUTINE_SETTING)
        self.assertEqual(
            routines,
            {
                "bad": {
                    "commands": [
                        {
                            "command": ("track", "0"),
                            "options": {},
                            "priority": 0,
                            "switches": (),
                        },
                        {
                            "command": ("does_not_exist",),
                            "options": {},
                            "priority": 0,
                            "switches": (),
                        },
                        {
                            "command": ("track", "1"),
                            "options": {},
                            "priority": 0,
                            "switches": (),
                        },
                    ],
                    "help_text": "Bad command test routine",
                    "name": "bad",
                    "switch_helps": {},
                },
                "deploy": {
                    "commands": [
                        {
                            "command": ("makemigrations",),
                            "options": {},
                            "priority": 0,
                            "switches": ["prepare"],
                        },
                        {
                            "command": ("migrate",),
                            "options": {},
                            "priority": 0,
                            "switches": (),
                        },
                        {
                            "command": ("renderstatic",),
                            "options": {},
                            "priority": 0,
                            "switches": (),
                        },
                        {
                            "command": ("collectstatic",),
                            "options": {},
                            "priority": 0,
                            "switches": (),
                        },
                        {
                            "command": ("shellcompletion", "install"),
                            "options": {},
                            "priority": 0,
                            "switches": ("initial",),
                        },
                        {
                            "command": ("loaddata", "./fixtures/initial_data.json"),
                            "options": {},
                            "priority": 0,
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
                        {
                            "command": ("track", "2"),
                            "options": {},
                            "priority": 0,
                            "switches": ("initial", "demo"),
                        },
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
                            "switches": (),
                        },
                        {
                            "command": ("track", "4"),
                            "options": {"demo": 6},
                            "priority": 3,
                            "switches": (),
                        },
                        {
                            "command": ("track", "1"),
                            "options": {},
                            "priority": 4,
                            "switches": (),
                        },
                        {
                            "command": ("track", "5"),
                            "options": {},
                            "priority": 6,
                            "switches": ("demo",),
                        },
                    ],
                    "help_text": "Test Routine 1",
                    "name": "test",
                    "switch_helps": {},
                },
            },
        )


@override_settings(
    INSTALLED_APPS=[
        "tests.django_routines_tests",
        "django_routines",
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
    ]
)
class NoDjangoTyperInstalledTests(Tests):
    pass


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
                {"command": ("track", "4"), "options": {"demo": 6}, "priority": 3},
                {"command": ("track", "1"), "priority": 4},
                {"command": ("track", "5"), "priority": 6, "switches": ("demo",)},
            ],
            "help_text": "Test Routine 1",
            "name": "test",
        },
    }
)
class SettingsAsDictTests(Tests):
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
                            "options": {"demo": 6},
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


@override_settings(
    DJANGO_ROUTINES={
        "bad": Routine(
            commands=[
                RoutineCommand(command=("track", "0")),
                RoutineCommand(command=("does_not_exist",)),
                RoutineCommand(command=("track", "1")),
            ],
            help_text="Bad command test routine",
            name="bad",
        ),
        "deploy": Routine(
            commands=[
                RoutineCommand(command=("makemigrations",), switches=["prepare"]),
                RoutineCommand(command=("migrate",)),
                RoutineCommand(command=("renderstatic",)),
                RoutineCommand(command=("collectstatic",)),
                RoutineCommand(
                    command=("shellcompletion", "install"), switches=("initial",)
                ),
                RoutineCommand(
                    command=("loaddata", "./fixtures/initial_data.json"),
                    switches=("demo",),
                ),
            ],
            help_text="Deploy the site application into production.",
            name="deploy",
            switch_helps={
                "demo": "Deploy the demo.",
                "prepare": "Prepare the deployment.",
            },
        ),
        "test": Routine(
            commands=[
                RoutineCommand(command=("track", "2"), switches=("initial", "demo")),
                RoutineCommand(
                    command=("track", "0"),
                    options={"verbosity": 0},
                    priority=1,
                    switches=("initial",),
                ),
                RoutineCommand(command=("track", "3"), options={"demo": 2}, priority=3),
                RoutineCommand(command=("track", "4"), options={"demo": 6}, priority=3),
                RoutineCommand(command=("track", "1"), priority=4),
                RoutineCommand(command=("track", "5"), priority=6, switches=("demo",)),
            ],
            help_text="Test Routine 1",
            name="test",
        ),
    }
)
class SettingsAsObjectsTests(Tests):
    def test_settings_format(self):
        routines = getattr(settings, ROUTINE_SETTING)
        self.assertEqual(
            routines,
            {
                "bad": Routine(
                    commands=[
                        RoutineCommand(command=("track", "0")),
                        RoutineCommand(command=("does_not_exist",)),
                        RoutineCommand(command=("track", "1")),
                    ],
                    help_text="Bad command test routine",
                    name="bad",
                ),
                "deploy": Routine(
                    commands=[
                        RoutineCommand(
                            command=("makemigrations",), switches=["prepare"]
                        ),
                        RoutineCommand(command=("migrate",)),
                        RoutineCommand(command=("renderstatic",)),
                        RoutineCommand(command=("collectstatic",)),
                        RoutineCommand(
                            command=("shellcompletion", "install"),
                            switches=("initial",),
                        ),
                        RoutineCommand(
                            command=("loaddata", "./fixtures/initial_data.json"),
                            switches=("demo",),
                        ),
                    ],
                    help_text="Deploy the site application into production.",
                    name="deploy",
                    switch_helps={
                        "demo": "Deploy the demo.",
                        "prepare": "Prepare the deployment.",
                    },
                ),
                "test": Routine(
                    commands=[
                        RoutineCommand(
                            command=("track", "2"), switches=("initial", "demo")
                        ),
                        RoutineCommand(
                            command=("track", "0"),
                            options={"verbosity": 0},
                            priority=1,
                            switches=("initial",),
                        ),
                        RoutineCommand(
                            command=("track", "3"), options={"demo": 2}, priority=3
                        ),
                        RoutineCommand(
                            command=("track", "4"), options={"demo": 6}, priority=3
                        ),
                        RoutineCommand(command=("track", "1"), priority=4),
                        RoutineCommand(
                            command=("track", "5"), priority=6, switches=("demo",)
                        ),
                    ],
                    help_text="Test Routine 1",
                    name="test",
                ),
            },
        )

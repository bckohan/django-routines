from io import StringIO
from importlib.util import find_spec
import pytest
import sys
from typing import Type, TYPE_CHECKING, TypeVar

from django.core.management import call_command, CommandError
from django_typer.management import get_command, TyperCommand
from django.test import TestCase
from django.conf import settings
from django_routines import ROUTINE_SETTING
import subprocess
import re
from tests import track_file
import json
import os
from pathlib import Path

from tests.django_routines_tests.management.commands.track import (
    invoked,
    passed_options,
)


manage_py = Path(__file__).parent.parent / "manage.py"

T = TypeVar("T")


def with_typehint(baseclass: Type[T]) -> Type[T]:
    """
    Change inheritance to add Field type hints when type checking is running.
    This is just more simple than defining a Protocol - revisit if Django
    provides Field protocol - should also just be a way to create a Protocol
    from a class?

    This is icky but it works - revisit in future.
    """
    if TYPE_CHECKING:
        return baseclass  # pragma: no cover
    return object  # type: ignore


class CoreTests(with_typehint(TestCase)):
    def setUp(self):
        if track_file.is_file():
            os.remove(track_file)
        super().setUp()

    def tearDown(self):
        if track_file.is_file():
            os.remove(track_file)
        super().setUp()

    def strip_ansi(self, text):
        ansi_escape = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")
        return ansi_escape.sub("", text)

    def lines(self, text, no_color):
        if no_color:
            self.assertTrue("\x1b" not in text)
        else:
            self.assertTrue("\x1b" in text)
        return [ln for ln in self.strip_ansi(text).strip().splitlines() if ln]

    def test_command(self, no_color=True, verbosity=None, subprocess=False):
        invoked.clear()
        passed_options.clear()
        clear_results = {"invoked": [], "passed_options": []}
        results = clear_results

        command = [
            "routine",
            *(["--manage-script", "./manage.py"] if subprocess else []),
            ("--no-color" if no_color else "--force-color"),
            *(("--verbosity", str(verbosity)) if verbosity is not None else tuple()),
            "test",
        ]
        if subprocess:
            command.append("--subprocess")
        out = StringIO()
        call_command(*command, stdout=out)
        expected = [3, 4, 1]
        if verbosity is None or verbosity > 0:
            for line, exp in zip(
                self.lines(out.getvalue(), no_color=no_color), expected
            ):
                self.assertTrue(f"track {exp}" in line)
        else:
            self.assertFalse(out.getvalue().strip())

        if subprocess:
            self.assertFalse(invoked)
            self.assertFalse(passed_options)
            results = json.loads(track_file.read_text())

        self.assertEqual(
            results["invoked"]
            if subprocess
            else results["invoked"]
            if subprocess
            else invoked,
            expected,
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[0]["demo"], 2
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[1]["demo"], 6
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[1]["flag"],
            True,
        )
        if verbosity is not None:
            for idx, opts in enumerate(passed_options):
                self.assertEqual(opts["verbosity"], verbosity)
        invoked.clear()
        passed_options.clear()
        track_file.write_text(json.dumps(clear_results))

        out = StringIO()
        call_command(*command, "--all", stdout=out)
        expected = [2, 0, 3, 4, 1, 5]
        if verbosity is None or verbosity > 0:
            for line, exp in zip(
                self.lines(out.getvalue(), no_color=no_color), expected
            ):
                self.assertTrue(f"track {exp}" in line)
        else:
            self.assertFalse(out.getvalue().strip())

        if subprocess:
            self.assertFalse(invoked)
            self.assertFalse(passed_options)
            results = json.loads(track_file.read_text())

        self.assertEqual(results["invoked"] if subprocess else invoked, expected)
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[1][
                "verbosity"
            ],
            0,
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[2]["demo"], 2
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[3]["demo"], 6
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[3]["flag"],
            True,
        )
        if verbosity is not None:
            for idx, opts in enumerate(passed_options):
                if idx != 1:
                    self.assertEqual(opts["verbosity"], verbosity)
        invoked.clear()
        passed_options.clear()
        track_file.write_text(json.dumps(clear_results))

        out = StringIO()
        call_command(*command, "--demo", stdout=out)
        expected = [2, 3, 4, 1, 5]
        if verbosity is None or verbosity > 0:
            for line, exp in zip(
                self.lines(out.getvalue(), no_color=no_color), expected
            ):
                self.assertTrue(f"track {exp}" in line)
        else:
            self.assertFalse(out.getvalue().strip())

        if subprocess:
            self.assertFalse(invoked)
            self.assertFalse(passed_options)
            results = json.loads(track_file.read_text())

        self.assertEqual(results["invoked"] if subprocess else invoked, expected)
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[1]["demo"], 2
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[2]["demo"], 6
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[2]["flag"],
            True,
        )
        if verbosity is not None:
            for idx, opts in enumerate(passed_options):
                self.assertEqual(opts["verbosity"], verbosity)
        invoked.clear()
        passed_options.clear()
        track_file.write_text(json.dumps(clear_results))

        out = StringIO()
        call_command(*command, "--demo", "--initial", stdout=out)
        expected = [2, 0, 3, 4, 1, 5]
        if verbosity is None or verbosity > 0:
            for line, exp in zip(
                self.lines(out.getvalue(), no_color=no_color), expected
            ):
                self.assertTrue(f"track {exp}" in line)
        else:
            self.assertFalse(out.getvalue().strip())

        if subprocess:
            self.assertFalse(invoked)
            self.assertFalse(passed_options)
            results = json.loads(track_file.read_text())

        self.assertEqual(results["invoked"] if subprocess else invoked, expected)
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[1][
                "verbosity"
            ],
            0,
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[2]["demo"], 2
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[3]["demo"], 6
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[3]["flag"],
            True,
        )
        if verbosity is not None:
            for idx, opts in enumerate(passed_options):
                if idx != 1:
                    self.assertEqual(opts["verbosity"], verbosity)
        invoked.clear()
        passed_options.clear()
        track_file.write_text(json.dumps(clear_results))

        out = StringIO()
        call_command(*command, "--initial", stdout=out)
        expected = [2, 0, 3, 4, 1]
        if verbosity is None or verbosity > 0:
            for line, exp in zip(
                self.lines(out.getvalue(), no_color=no_color), expected
            ):
                self.assertTrue(f"track {exp}" in line)
        else:
            self.assertFalse(out.getvalue().strip())

        if subprocess:
            self.assertFalse(invoked)
            self.assertFalse(passed_options)
            results = json.loads(track_file.read_text())

        self.assertEqual(results["invoked"] if subprocess else invoked, expected)
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[1][
                "verbosity"
            ],
            0,
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[2]["demo"], 2
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[3]["demo"], 6
        )
        self.assertEqual(
            (results["passed_options"] if subprocess else passed_options)[3]["flag"],
            True,
        )
        if verbosity is not None:
            for idx, opts in enumerate(passed_options):
                if idx != 1:
                    self.assertEqual(opts["verbosity"], verbosity)
        invoked.clear()
        passed_options.clear()
        track_file.write_text(json.dumps(clear_results))

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
                "[3] track 4 (demo=6, flag=True)",
                "[4] track 1",
                "[6] track 5 | demo",
            ],
        )

        out = StringIO()
        call_command(*command, "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            ["[3] track 3 (demo=2)", "[3] track 4 (demo=6, flag=True)", "[4] track 1"],
        )

        out = StringIO()
        call_command(*command, "--demo", "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[0] track 2 | initial, demo",
                "[3] track 3 (demo=2)",
                "[3] track 4 (demo=6, flag=True)",
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
                "[3] track 4 (demo=6, flag=True)",
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
                "[3] track 4 (demo=6, flag=True)",
                "[4] track 1",
            ],
        )

    def test_list_color(self):
        self.test_list(no_color=False)

    def test_routine_with_bad_command(self):
        with self.assertRaises(CommandError):
            call_command("routine", "bad")

    def test_subprocess(self):
        self.test_command(subprocess=True)

    routine_help_rich = """
 Usage: ./manage.py routine [OPTIONS] COMMAND [ARGS]...                         
                                                                                
 Run batches of commands configured in settings.                                
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --manage-script        TEXT  The manage script to use if running management  │
│                              commands as subprocesses.                       │
│                              [default: manage.py]                            │
│ --help                       Show this message and exit.                     │
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
 [3] track 4 (demo=6, flag=True)                                                
 [4] track 1                                                                    
 [6] track 5 | demo                                                             
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --subprocess          Run commands as subprocesses.                          │
│ --all                 Include all switched commands.                         │
│ --demo                                                                       │
│ --initial                                                                    │
│ --help                Show this message and exit.                            │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ list   List the commands that will be run.                                   │
╰──────────────────────────────────────────────────────────────────────────────╯
"""

    @pytest.mark.skipif(find_spec("rich") is None, reason="Rich is not installed.")
    def test_helps_rich(self):
        result = subprocess.run(
            [
                sys.executable,
                manage_py.relative_to(Path(os.getcwd())),
                "routine",
                "--help",
            ],
            env=os.environ.copy(),
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertFalse(result.stderr)
        self.assertEqual(result.stdout.decode().strip(), self.routine_help_rich.strip())

        stdout = StringIO()

        routine = get_command("routine", TyperCommand, stdout=stdout, no_color=True)
        routine.print_help("./manage.py", "routine", "test")
        self.assertEqual(
            stdout.getvalue().strip().replace("\x08", ""),
            self.routine_test_help_rich.strip(),
        )

    routine_help_no_rich = """
Usage: ./manage.py routine [OPTIONS] COMMAND [ARGS]...

  Run batches of commands configured in settings.

Options:
  --manage-script TEXT       The manage script to use if running management
                             commands as subprocesses.  [default: manage.py]
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
  [3] track 4 (demo=6, flag=True)
  [4] track 1
  [6] track 5 | demo

Options:
  --subprocess  Run commands as subprocesses.
  --all         Include all switched commands.
  --demo
  --initial
  --help        Show this message and exit.

Commands:
  list  List the commands that will be run.
"""

    @pytest.mark.skipif(find_spec("rich") is not None, reason="Rich is installed.")
    def test_helps_no_rich(self):
        result = subprocess.run(
            [
                sys.executable,
                manage_py.relative_to(Path(os.getcwd())),
                "routine",
                "--help",
            ],
            env=os.environ.copy(),
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertFalse(result.stderr)
        self.assertEqual(
            result.stdout.strip().decode(),
            self.routine_help_no_rich.format(script=sys.argv[0]).strip(),
        )

        stdout = StringIO()

        routine = get_command("routine", TyperCommand, stdout=stdout, no_color=True)
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
                    "subprocess": False,
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
                    "subprocess": False,
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
                            "options": {"demo": 6, "flag": True},
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
                    "subprocess": False,
                },
            },
        )


class Test(CoreTests, TestCase):
    pass

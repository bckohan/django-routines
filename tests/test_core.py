from io import StringIO
from importlib.util import find_spec
import pytest
import sys
from typing import Type, TYPE_CHECKING, TypeVar
from tests.django_routines_tests.models import TestModel as _TestModel
from collections import Counter
import math

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
    TestError,
)

WORD = re.compile(r"\w+")


def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
    sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator


def text_to_vector(text):
    words = WORD.findall(text)
    return Counter(words)


def similarity(text1, text2):
    """
    Compute the cosine similarity between two texts.
    https://en.wikipedia.org/wiki/Cosine_similarity

    We use this to lazily evaluate the output of --help to our
    renderings.
    #"""
    vector1 = text_to_vector(text1)
    vector2 = text_to_vector(text2)
    return get_cosine(vector1, vector2)


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
        _TestModel.objects.create(id=0, name="Brian")
        super().setUp()

    def tearDown(self):
        if track_file.is_file():
            os.remove(track_file)
        _TestModel.objects.all().delete()
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
            "import",
        ]
        if subprocess:
            command.append("--subprocess")
        out = StringIO()
        err = StringIO()
        call_command(*command, stdout=out, stderr=err)
        expected = [3, 4, 1]
        sys_expected = ["sys 1", "sys 2"]
        if verbosity is None or verbosity > 0:
            for line, exp in zip(
                self.lines(out.getvalue(), no_color=no_color),
                [
                    *[f"track {exp}" for exp in expected],
                    *[f"system_cmd.py {exp}" for exp in sys_expected],
                ],
            ):
                self.assertTrue(exp in line)
        else:
            self.assertTrue("track" not in out.getvalue().strip())
            self.assertTrue("system_cmd" not in out.getvalue().strip())

        if subprocess:
            self.assertFalse(invoked)
            self.assertFalse(passed_options)
        results = json.loads(track_file.read_text())

        self.assertEqual(
            results["invoked"] if subprocess else invoked,
            expected + sys_expected if subprocess else expected,
        )
        self.assertEqual(results["invoked"], [*expected, *sys_expected])
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
                self.lines(out.getvalue(), no_color=no_color),
                [
                    *[f"track {exp}" for exp in expected],
                    *[f"system_cmd.py {exp}" for exp in sys_expected],
                ],
            ):
                self.assertTrue(exp in line)
        else:
            self.assertTrue("track" not in out.getvalue().strip())
            self.assertTrue("system_cmd" not in out.getvalue().strip())

        if subprocess:
            self.assertFalse(invoked)
            self.assertFalse(passed_options)
        results = json.loads(track_file.read_text())

        self.assertEqual(
            results["invoked"] if subprocess else invoked,
            expected + sys_expected if subprocess else expected,
        )
        self.assertEqual(results["invoked"], [*expected, *sys_expected])
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
                self.lines(out.getvalue(), no_color=no_color),
                [
                    *[f"track {exp}" for exp in expected],
                    *[f"system_cmd.py {exp}" for exp in sys_expected],
                ],
            ):
                self.assertTrue(exp in line)
        else:
            self.assertTrue("track" not in out.getvalue().strip())
            self.assertTrue("system_cmd" not in out.getvalue().strip())

        if subprocess:
            self.assertFalse(invoked)
            self.assertFalse(passed_options)
        results = json.loads(track_file.read_text())

        self.assertEqual(
            results["invoked"] if subprocess else invoked,
            expected + sys_expected if subprocess else expected,
        )
        self.assertEqual(results["invoked"], [*expected, *sys_expected])
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
        call_command(*command, "--demo", "--import", stdout=out)
        expected = [2, 0, 3, 4, 1, 5]
        if verbosity is None or verbosity > 0:
            for line, exp in zip(
                self.lines(out.getvalue(), no_color=no_color),
                [
                    *[f"track {exp}" for exp in expected],
                    *[f"system_cmd.py {exp}" for exp in sys_expected],
                ],
            ):
                self.assertTrue(exp in line)
        else:
            self.assertTrue("track" not in out.getvalue().strip())
            self.assertTrue("system_cmd" not in out.getvalue().strip())

        if subprocess:
            self.assertFalse(invoked)
            self.assertFalse(passed_options)
        results = json.loads(track_file.read_text())

        self.assertEqual(
            results["invoked"] if subprocess else invoked,
            expected + sys_expected if subprocess else expected,
        )
        self.assertEqual(results["invoked"], [*expected, *sys_expected])
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
        call_command(*command, "--import", stdout=out)
        expected = [2, 0, 3, 4, 1]
        if verbosity is None or verbosity > 0:
            for line, exp in zip(
                self.lines(out.getvalue(), no_color=no_color),
                [
                    *[f"track {exp}" for exp in expected],
                    *[f"system_cmd.py {exp}" for exp in sys_expected],
                ],
            ):
                self.assertTrue(exp in line)
        else:
            self.assertTrue("track" not in out.getvalue().strip())
            self.assertTrue("system_cmd" not in out.getvalue().strip())

        if subprocess:
            self.assertFalse(invoked)
            self.assertFalse(passed_options)
        results = json.loads(track_file.read_text())

        self.assertEqual(
            results["invoked"] if subprocess else invoked,
            expected + sys_expected if subprocess else expected,
        )
        self.assertEqual(results["invoked"], [*expected, *sys_expected])
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
            command = ("routine", "--no-color", "import")
        else:
            command = ("routine", "--force-color", "import")

        out = StringIO()
        call_command(*command, "--all", "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[0] track 2 | import, demo",
                "[1] track 0 (verbosity=0) | import",
                "[3] track 3 (demo=2)",
                "[3] track 4 (demo=6, flag=True)",
                "[4] track 1",
                "[6] track 5 | demo",
                f"[7] python tests{os.sep}system_cmd.py sys 1",
                f"[8] python tests{os.sep}system_cmd.py sys 2",
            ],
        )

        out = StringIO()
        call_command(*command, "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[3] track 3 (demo=2)",
                "[3] track 4 (demo=6, flag=True)",
                "[4] track 1",
                f"[7] python tests{os.sep}system_cmd.py sys 1",
                f"[8] python tests{os.sep}system_cmd.py sys 2",
            ],
        )

        out = StringIO()
        call_command(*command, "--demo", "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[0] track 2 | import, demo",
                "[3] track 3 (demo=2)",
                "[3] track 4 (demo=6, flag=True)",
                "[4] track 1",
                "[6] track 5 | demo",
                f"[7] python tests{os.sep}system_cmd.py sys 1",
                f"[8] python tests{os.sep}system_cmd.py sys 2",
            ],
        )

        out = StringIO()
        call_command(*command, "--demo", "--import", "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[0] track 2 | import, demo",
                "[1] track 0 (verbosity=0) | import",
                "[3] track 3 (demo=2)",
                "[3] track 4 (demo=6, flag=True)",
                "[4] track 1",
                "[6] track 5 | demo",
                f"[7] python tests{os.sep}system_cmd.py sys 1",
                f"[8] python tests{os.sep}system_cmd.py sys 2",
            ],
        )

        out = StringIO()
        call_command(*command, "--import", "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[0] track 2 | import, demo",
                "[1] track 0 (verbosity=0) | import",
                "[3] track 3 (demo=2)",
                "[3] track 4 (demo=6, flag=True)",
                "[4] track 1",
                f"[7] python tests{os.sep}system_cmd.py sys 1",
                f"[8] python tests{os.sep}system_cmd.py sys 2",
            ],
        )

    def test_hyphen_list(self, no_color=True):
        if no_color:
            command = ("routine", "--no-color", "test-hyphen")
        else:
            command = ("routine", "--force-color", "test-hyphen")

        out = StringIO()
        call_command(*command, "--all", "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[0] track 1 | hyphen-ok, hyphen-ok-prefix",
                "[0] track 2",
                "[0] track 3 | hyphen-ok",
                "[0] track 4",
                "[0] track 5 | hyphen-ok, hyphen-ok-prefix",
            ],
        )

        out = StringIO()
        call_command(*command, "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            ["[0] track 2", "[0] track 4"],
        )

        out = StringIO()
        call_command(*command, "--hyphen-ok", "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[0] track 1 | hyphen-ok, hyphen-ok-prefix",
                "[0] track 2",
                "[0] track 3 | hyphen-ok",
                "[0] track 4",
                "[0] track 5 | hyphen-ok, hyphen-ok-prefix",
            ],
        )

        out = StringIO()
        call_command(*command, "--hyphen-ok-prefix", "list", stdout=out)
        plan = self.lines(out.getvalue(), no_color=no_color)
        self.assertEqual(
            plan,
            [
                "[0] track 1 | hyphen-ok, hyphen-ok-prefix",
                "[0] track 2",
                "[0] track 4",
                "[0] track 5 | hyphen-ok, hyphen-ok-prefix",
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
│ --traceback                                   Raise on CommandError          │
│                                               exceptions                     │
│ --show-locals                                 Print local variables in       │
│                                               tracebacks.                    │
│ --no-color                                    Don't colorize the command     │
│                                               output.                        │
│ --force-color                                 Force colorization of the      │
│                                               command output.                │
│ --skip-checks                                 Skip system checks.            │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ deploy          Deploy the site application into production.                 │
│ import          Test Routine 1                                               │
│ bad             Bad command test routine                                     │
│ test-hyphen     Test that hyphens dont mess everything up.                   │
│ atomic-pass     Atomic test routine.                                         │
│ atomic-fail     Atomic test routine failure.                                 │
│ test-continue   Test continue option.                                        │
╰──────────────────────────────────────────────────────────────────────────────╯
"""

    routine_test_help_rich = f"""
 Usage: ./manage.py routine import [OPTIONS] COMMAND [ARGS]...                  
                                                                                
                                                                                
 Test Routine 1                                                                 
                                                                                
                                                                                
 [0] track 2 | import, demo                                                     
 [1] track 0 (verbosity=0) | import                                             
 [3] track 3 (demo=2)                                                           
 [3] track 4 (demo=6, flag=True)                                                
 [4] track 1                                                                    
 [6] track 5 | demo                                                             
 [7] python tests{os.sep}system_cmd.py sys 1                                                  
 [8] python tests{os.sep}system_cmd.py sys 2                                                  
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --subprocess          Run commands as subprocesses.                          │
│ --atomic              Run all commands in the same transaction.              │
│ --continue            Continue through the routine if any commands fail.     │
│ --all                 Include all switched commands.                         │
│ --demo                                                                       │
│ --import                                                                     │
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
            env={**os.environ.copy(), "PYTHONIOENCODING": "utf-8"},
            capture_output=True,
        )
        self.assertEqual(
            result.returncode, 0, (result.stderr or result.stdout).decode()
        )
        self.assertFalse(result.stderr)
        hlp_txt = self.strip_ansi(result.stdout.decode()).strip()
        expected = self.routine_help_rich.strip()
        self.assertGreater(similarity(hlp_txt, expected), 0.99)

        stdout = StringIO()

        routine = get_command("routine", TyperCommand, stdout=stdout, no_color=True)
        routine.print_help("./manage.py", "routine", "import")
        self.assertGreater(
            similarity(
                self.strip_ansi(stdout.getvalue()).strip().replace("\x08", ""),
                self.routine_test_help_rich.strip(),
            ),
            0.99,
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
  deploy         Deploy the site application into production.
  import         Test Routine 1
  bad            Bad command test routine
  test-hyphen    Test that hyphens dont mess everything up.
  atomic-pass    Atomic test routine.
  atomic-fail    Atomic test routine failure.
  test-continue  Test continue option.
"""

    routine_test_help_no_rich = f"""
Usage: ./manage.py routine import [OPTIONS] COMMAND [ARGS]...

  Test Routine 1
  ----------------------------------
  
  [0] track 2 | import, demo
  [1] track 0 (verbosity=0) | import
  [3] track 3 (demo=2)
  [3] track 4 (demo=6, flag=True)
  [4] track 1
  [6] track 5 | demo
  [7] python tests{os.sep}system_cmd.py sys 1
  [8] python tests{os.sep}system_cmd.py sys 2

Options:
  --subprocess  Run commands as subprocesses.
  --atomic      Run all commands in the same transaction.
  --continue    Continue through the routine if any commands fail.
  --all         Include all switched commands.
  --demo
  --import
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
        self.assertGreater(
            similarity(
                result.stdout.strip().decode(),
                self.routine_help_no_rich.format(script=sys.argv[0]).strip(),
            ),
            0.99,
        )

        stdout = StringIO()

        routine = get_command("routine", TyperCommand, stdout=stdout, no_color=True)
        routine.print_help("./manage.py", "routine", "import")
        printed = stdout.getvalue().strip().replace("\x08", "")
        expected = self.routine_test_help_no_rich
        self.assertGreater(similarity(printed, expected), 0.99)

    def test_settings_format(self):
        routines = getattr(settings, ROUTINE_SETTING)
        self.assertEqual(
            routines["bad"],
            {
                "commands": [
                    {
                        "command": ("track", "0"),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": (),
                    },
                    {
                        "command": ("does_not_exist",),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": (),
                    },
                    {
                        "command": ("track", "1"),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": (),
                    },
                ],
                "help_text": "Bad command test routine",
                "name": "bad",
                "switch_helps": {},
                "subprocess": False,
                "atomic": False,
                "continue_on_error": False,
            },
        )
        self.assertEqual(
            routines["deploy"],
            {
                "commands": [
                    {
                        "command": ("makemigrations",),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": ("prepare",),
                    },
                    {
                        "command": ("migrate",),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": (),
                    },
                    {
                        "command": ("renderstatic",),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": (),
                    },
                    {
                        "command": "collectstatic",
                        "kind": "management",
                        "options": {"interactive": False},
                        "priority": 0,
                        "switches": (),
                    },
                    {
                        "command": ("shellcompletion", "install"),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": ("import",),
                    },
                    {
                        "command": ("loaddata", "./fixtures/initial_data.json"),
                        "kind": "management",
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
                "atomic": False,
                "continue_on_error": False,
            },
        )
        self.assertEqual(
            routines["import"],
            {
                "commands": [
                    {
                        "command": ("track", "2"),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": ("import", "demo"),
                    },
                    {
                        "command": ("track", "0"),
                        "kind": "management",
                        "options": {"verbosity": 0},
                        "priority": 1,
                        "switches": ("import",),
                    },
                    {
                        "command": ("track", "3"),
                        "kind": "management",
                        "options": {"demo": 2},
                        "priority": 3,
                        "switches": (),
                    },
                    {
                        "command": ("track", "4"),
                        "kind": "management",
                        "options": {"demo": 6, "flag": True},
                        "priority": 3,
                        "switches": (),
                    },
                    {
                        "command": ("track", "1"),
                        "kind": "management",
                        "options": {},
                        "priority": 4,
                        "switches": (),
                    },
                    {
                        "command": ("track", "5"),
                        "kind": "management",
                        "options": {},
                        "priority": 6,
                        "switches": ("demo",),
                    },
                    {
                        "command": ("python", f"tests{os.sep}system_cmd.py", "sys 1"),
                        "kind": "system",
                        "priority": 7,
                        "switches": (),
                    },
                    {
                        "command": ("python", f"tests{os.sep}system_cmd.py", "sys 2"),
                        "kind": "system",
                        "priority": 8,
                        "switches": (),
                    },
                ],
                "help_text": "Test Routine 1",
                "name": "import",
                "switch_helps": {},
                "subprocess": False,
                "atomic": False,
                "continue_on_error": False,
            },
        )
        self.assertEqual(
            routines["test_hyphen"],
            {
                "commands": [
                    {
                        "command": ("track", "1"),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": ("hyphen_ok", "hyphen_ok_prefix"),
                    },
                    {
                        "command": ("track", "2"),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": (),
                    },
                    {
                        "command": ("track", "3"),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": ("hyphen_ok",),
                    },
                    {
                        "command": ("track", "4"),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": (),
                    },
                    {
                        "command": ("track", "5"),
                        "kind": "management",
                        "options": {},
                        "priority": 0,
                        "switches": ("hyphen_ok", "hyphen_ok_prefix"),
                    },
                ],
                "help_text": "Test that hyphens dont mess everything up.",
                "name": "test_hyphen",
                "subprocess": False,
                "atomic": False,
                "continue_on_error": False,
                "switch_helps": {
                    "hyphen_ok": "Test hyphen.",
                    "hyphen_ok_prefix": "Test hyphen with -- prefix.",
                },
            },
        )

    def test_non_atomic(self):
        call_command("routine", "atomic-pass")
        self.assertEqual(_TestModel.objects.get(id=0).name, "Name3")
        self.assertEqual(_TestModel.objects.get(id=1).name, "Name4")
        self.assertEqual(_TestModel.objects.count(), 2)

    def test_force_nonatomic(self):
        call_command("routine", "atomic-pass", "--non-atomic")
        self.assertEqual(_TestModel.objects.get(id=0).name, "Name3")
        self.assertEqual(_TestModel.objects.get(id=1).name, "Name4")
        self.assertEqual(_TestModel.objects.count(), 2)

    def test_atomic_fail(self):
        with self.assertRaises(TestError):
            call_command("routine", "atomic-fail")
        self.assertEqual(_TestModel.objects.get(id=0).name, "Brian")
        self.assertEqual(_TestModel.objects.count(), 1)

    def test_force_nonatomic_fail(self):
        with self.assertRaises(TestError):
            call_command("routine", "atomic-fail", "--non-atomic")
        self.assertEqual(_TestModel.objects.get(id=0).name, "Name3")
        self.assertEqual(_TestModel.objects.count(), 1)

    def test_force_atomic_continue_fail(self):
        call_command("routine", "atomic-fail", "--continue")
        self.assertEqual(_TestModel.objects.get(id=0).name, "Name3")
        self.assertEqual(_TestModel.objects.count(), 1)

    def test_continue_on_error(self):
        call_command("routine", "test-continue")
        self.assertEqual(_TestModel.objects.get(id=0).name, "Name3")

    def test_force_halt_on_error(self):
        with self.assertRaises(TestError):
            call_command("routine", "test-continue", "--halt")
        self.assertEqual(_TestModel.objects.get(id=0).name, "Name1")


class Test(CoreTests, TestCase):
    pass

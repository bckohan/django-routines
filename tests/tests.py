from io import StringIO

from django.core.management import call_command, CommandError
from django.test import TestCase
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

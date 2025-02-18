"""
Miscellaneous tests - mostly for coverage
"""

from io import StringIO
import sys
import subprocess
from django.core.management import call_command
from django.test import TestCase
import pexpect


class TestDeploy(TestCase):
    def test_deploy_routine(self):
        out = StringIO()
        err = StringIO()
        call_command("routine", "deploy", "--prepare", stdout=out, stderr=err)
        self.assertTrue(out.getvalue())
        self.assertFalse(err.getvalue().strip())


def test_subprocess_error():
    result = subprocess.run(
        [
            sys.executable,
            "./manage.py",
            "routine",
            "--settings",
            "tests.settings_subproc_error",
            "subproc-error",
            "--subprocess",
        ],
        text=True,
        capture_output=True,
    )

    assert "panic!" in result.stderr
    assert "Subprocess command failed" in result.stderr


def test_subprocess_opt_error():
    result = subprocess.run(
        [
            sys.executable,
            "./manage.py",
            "routine",
            "--settings",
            "tests.settings_subproc_opt_error",
            "subproc-opt-error",
            "--subprocess",
        ],
        text=True,
        capture_output=True,
    )

    assert (
        "CommandError: Failed to convert collectstatic options to CLI format: {'not-an-option': False}"
        in result.stderr
    )


def test_option_toggle():
    child = pexpect.spawn(
        " ".join(
            [
                sys.executable,
                "./manage.py",
                "routine",
                "--settings",
                "tests.settings_option_toggle",
                "option-on",
                "--subprocess",
            ]
        )
    )
    child.expect("static files copied.")

    child = pexpect.spawn(
        " ".join(
            [
                sys.executable,
                "./manage.py",
                "routine",
                "--settings",
                "tests.settings_option_toggle",
                "option-off",
                "--subprocess",
            ]
        )
    )
    child.expect("Type 'yes' to continue, or 'no' to cancel:")
    child.sendline("yes")
    child.expect("static files copied.")

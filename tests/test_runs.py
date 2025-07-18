"""
Miscellaneous tests - mostly for coverage
"""

from io import StringIO
import sys
import subprocess
from django.core.management import call_command
from django.test import TestCase
import pexpect
import platform


class TestDeploy(TestCase):
    def test_deploy_routine(self):
        out = StringIO()
        err = StringIO()
        call_command("routine", "deploy", "--prepare", stdout=out, stderr=err)
        self.assertTrue(out.getvalue())
        self.assertTrue(
            "makemigrations" in out.getvalue()
            and "migrate" in out.getvalue()
            and "renderstatic" in out.getvalue()
            and "collectstatic" in out.getvalue()
        )
        self.assertFalse(err.getvalue().strip())

    def test_deploy_routine_subprocess(self):
        out = StringIO()
        err = StringIO()
        call_command(
            "routine",
            "deploy",
            "--prepare",
            stdout=out,
            stderr=err,
            subprocess=True,
            manage_script="./manage.py",
        )
        self.assertTrue(out.getvalue(), err.getvalue())
        self.assertTrue(
            "makemigrations" in out.getvalue()
            and "migrate" in out.getvalue()
            and "renderstatic" in out.getvalue()
            and "collectstatic" in out.getvalue()
        )
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


if platform.system() == "Windows":
    from winpty import PtyProcess
    import time

    def test_option_toggle():
        result = subprocess.run(
            [
                sys.executable,
                "./manage.py",
                "routine",
                "--settings",
                "tests.settings_option_toggle",
                "option-on",
                "--subprocess",
            ],
            text=True,
            capture_output=True,
        )

        assert "static files copied." in result.stdout

        proc = PtyProcess.spawn(
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
        time.sleep(3)
        initial_output = proc.read(1024)
        assert "Type 'yes' to continue, or 'no' to cancel:" in initial_output
        proc.write("yes\r\n")
        time.sleep(3)
        dir_output = proc.read(4096)
        assert "static files copied." in dir_output
else:

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

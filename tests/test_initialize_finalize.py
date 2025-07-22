import importlib
import typing as t
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
from tests import track_file

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


def load_track_file() -> t.Dict[str, t.Any]:
    """Load the track file, creating it if it doesn't exist."""
    if not track_file.is_file():
        track_file.write_text(
            json.dumps(
                {"invoked": [], "initialize": [], "finalize": [], "passed_options": []},
                indent=4,
            )
        )
    track = json.loads(track_file.read_text())
    track.setdefault("invoked", [])
    track.setdefault("initialize", [])
    track.setdefault("finalize", [])
    track.setdefault("passed_options", [])
    return track


def initialize_track(routine, plan, switches, options):
    """Initialize callback that tracks routine startup."""
    track = load_track_file()
    track["initialize"].append(
        {
            "routine_name": routine.name,
            "plan_count": len(plan),
            "plan_commands": [cmd.command_str for cmd in plan],
            "switches": sorted(list(switches)),
            "options": options,
        }
    )
    track_file.write_text(json.dumps(track, indent=4))


def finalize_track(routine, results):
    """Finalize callback that tracks routine completion."""
    track = load_track_file()
    track["finalize"].append(
        {
            "routine_name": routine.name,
            "results_count": len(results),
            "results": [str(result) for result in results if result is not None],
        }
    )
    track_file.write_text(json.dumps(track, indent=4))


def initialize_modify_plan(routine, plan, switches, options):
    """Initialize callback that modifies the execution plan."""
    initialize_track(routine, plan, switches, options)
    # Modify a command in the plan
    if plan and hasattr(plan[0], "command"):
        parts = list(plan[0].command)
        if len(parts) > 1 and parts[-1].isdigit():
            parts[-1] = str(int(parts[-1]) + 100)
            plan[0].command = tuple(parts)


def finalize_modify_results(routine, results):
    """Finalize callback that modifies results."""
    # Add a marker to show finalize ran
    results.append("finalize_marker")
    finalize_track(routine, results)


class InitializeFinalizeTests(TestCase):
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
            "routine-init-final": Routine(
                commands=[
                    ManagementCommand(command=("track", "0"), switches=["switch"]),
                    ManagementCommand(command=("track", "1")),
                    ManagementCommand(command=("track", "2")),
                    SystemCommand(command=(*system_cmd, "track 3")),
                ],
                help_text="Test initialize and finalize callbacks.",
                initialize="tests.test_initialize_finalize.initialize_track",
                finalize="tests.test_initialize_finalize.finalize_track",
                name="routine-init-final",
            ),
        }
    )
    def test_initialize_finalize_callbacks(self):
        self.reload()
        call_command("routine", "--no-color", "routine-init-final", "--switch")
        track = load_track_file()

        # Test that both initialize and finalize were called
        self.assertEqual(len(track["initialize"]), 1)
        self.assertEqual(len(track["finalize"]), 1)

        # Test initialize callback data
        init_data = track["initialize"][0]
        self.assertEqual(init_data["routine_name"], "routine_init_final")
        self.assertEqual(init_data["plan_count"], 4)
        self.assertEqual(len(init_data["plan_commands"]), 4)
        self.assertEqual(init_data["switches"], ["switch"])

        # Verify initialize options
        expected_options = {
            **DEFAULT_OPTIONS,
            "no_color": True,
            "switch": True,
        }
        init_opts = init_data["options"]
        del init_opts["manage_script"]  # Remove variable path
        self.assertDictEqual(init_opts, expected_options)

        # Test finalize callback data
        final_data = track["finalize"][0]
        self.assertEqual(final_data["routine_name"], "routine_init_final")
        self.assertEqual(final_data["results_count"], 4)

        # Test that all commands were invoked
        self.assertEqual(track["invoked"], [0, 1, 2, "track 3"])

    @override_settings(
        DJANGO_ROUTINES={
            "routine-init-final": Routine(
                commands=[
                    ManagementCommand(command=("track", "5")),
                    ManagementCommand(command=("track", "6")),
                ],
                help_text="Test initialize callback modifying execution plan.",
                initialize=initialize_modify_plan,
                finalize=finalize_modify_results,
                name="routine-init-final",
            ),
        }
    )
    def test_initialize_modify_plan(self):
        self.reload()
        call_command("routine", "routine-init-final")
        track = load_track_file()

        # Test that initialize was called
        self.assertEqual(len(track["initialize"]), 1)
        init_data = track["initialize"][0]
        self.assertEqual(init_data["routine_name"], "routine_init_final")

        # Test that the first command was modified (5 + 100 = 105)
        self.assertEqual(track["invoked"], [105, 6])

        # Test that finalize was called and modified results
        self.assertEqual(len(track["finalize"]), 1)
        final_data = track["finalize"][0]
        # Results should include the finalize marker
        self.assertIn("finalize_marker", final_data["results"])

    @override_settings(
        DJANGO_ROUTINES={
            "routine-init-only": Routine(
                commands=[
                    ManagementCommand(command=("track", "10")),
                    ManagementCommand(command=("track", "11")),
                ],
                help_text="Test initialize callback only.",
                initialize="tests.test_initialize_finalize.initialize_track",
                name="routine-init-only",
            ),
        }
    )
    def test_initialize_only(self):
        self.reload()
        call_command("routine", "routine-init-only")
        track = load_track_file()

        # Test that initialize was called but finalize was not
        self.assertEqual(len(track["initialize"]), 1)
        self.assertEqual(len(track["finalize"]), 0)

        init_data = track["initialize"][0]
        self.assertEqual(init_data["routine_name"], "routine_init_only")
        self.assertEqual(init_data["plan_count"], 2)
        self.assertEqual(track["invoked"], [10, 11])
        self.assertEqual(init_data["plan_commands"], ["track 10", "track 11"])
        self.assertEqual(init_data["switches"], [])

    @override_settings(
        DJANGO_ROUTINES={
            "routine-final-only": Routine(
                commands=[
                    ManagementCommand(command=("track", "20")),
                    ManagementCommand(command=("track", "21")),
                ],
                help_text="Test finalize callback only.",
                finalize="tests.test_initialize_finalize.finalize_track",
                name="routine-final-only",
            ),
        }
    )
    def test_finalize_only(self):
        self.reload()
        call_command("routine", "routine-final-only")
        track = load_track_file()

        # Test that finalize was called but initialize was not
        self.assertEqual(len(track["initialize"]), 0)
        self.assertEqual(len(track["finalize"]), 1)

        final_data = track["finalize"][0]
        self.assertEqual(final_data["routine_name"], "routine_final_only")
        self.assertEqual(final_data["results_count"], 2)
        self.assertEqual(track["invoked"], [20, 21])

    @override_settings(
        DJANGO_ROUTINES={
            "routine-no-switches": Routine(
                commands=[
                    ManagementCommand(command=("track", "30"), switches=["switch1"]),
                    ManagementCommand(command=("track", "31"), switches=["switch2"]),
                    ManagementCommand(command=("track", "32")),
                ],
                help_text="Test initialize with filtered commands.",
                initialize="tests.test_initialize_finalize.initialize_track",
                finalize="tests.test_initialize_finalize.finalize_track",
                name="routine-no-switches",
            ),
        }
    )
    def test_initialize_filtered_commands(self):
        """Test initialize callback with commands filtered by switches."""
        self.reload()
        call_command("routine", "routine-no-switches")
        track = load_track_file()

        # Only one command should run (without switches)
        self.assertEqual(track["invoked"], [32])

        # Initialize should see the filtered plan
        init_data = track["initialize"][0]
        self.assertEqual(init_data["plan_count"], 1)
        self.assertEqual(init_data["plan_commands"], ["track 32"])
        self.assertEqual(init_data["switches"], [])

        # Finalize should see results from one command
        final_data = track["finalize"][0]
        self.assertEqual(final_data["results_count"], 1)

    @override_settings(
        DJANGO_ROUTINES={
            "routine-with-switches": Routine(
                commands=[
                    ManagementCommand(command=("track", "40"), switches=["switch1"]),
                    ManagementCommand(command=("track", "41"), switches=["switch2"]),
                    ManagementCommand(command=("track", "42")),
                ],
                help_text="Test initialize with switch activation.",
                initialize="tests.test_initialize_finalize.initialize_track",
                finalize="tests.test_initialize_finalize.finalize_track",
                name="routine-with-switches",
            ),
        }
    )
    def test_initialize_with_switches(self):
        """Test initialize callback with specific switches activated."""
        self.reload()
        call_command("routine", "routine-with-switches", "--switch1")
        track = load_track_file()

        # Two commands should run (one with switch1, one without switches)
        self.assertEqual(track["invoked"], [40, 42])

        # Initialize should see the filtered plan
        init_data = track["initialize"][0]
        self.assertEqual(init_data["plan_count"], 2)
        self.assertEqual(init_data["switches"], ["switch1"])

        # Finalize should see results from two commands
        final_data = track["finalize"][0]
        self.assertEqual(final_data["results_count"], 2)

    @override_settings(
        DJANGO_ROUTINES={
            "routine-mixed-commands": Routine(
                commands=[
                    ManagementCommand(command=("track", "50")),
                    SystemCommand(command=(*system_cmd, "track 51")),
                    ManagementCommand(command=("track", "52")),
                ],
                help_text="Test callbacks with mixed command types.",
                initialize="tests.test_initialize_finalize.initialize_track",
                finalize="tests.test_initialize_finalize.finalize_track",
                name="routine-mixed-commands",
            ),
        }
    )
    def test_initialize_finalize_mixed_commands(self):
        """Test initialize and finalize with mix of management and system commands."""
        self.reload()
        call_command("routine", "routine-mixed-commands")
        track = load_track_file()

        # All commands should run
        self.assertEqual(track["invoked"], [50, "track 51", 52])

        # Initialize should see all commands in plan
        init_data = track["initialize"][0]
        self.assertEqual(init_data["plan_count"], 3)
        self.assertEqual(len(init_data["plan_commands"]), 3)

        # Finalize should see results from all commands
        final_data = track["finalize"][0]
        self.assertEqual(final_data["results_count"], 3)

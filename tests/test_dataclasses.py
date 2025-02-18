import os
from django.test import TestCase, override_settings
from django_routines import ROUTINE_SETTING, Routine, RoutineCommand, SystemCommand
from django.conf import settings
from .test_core import CoreTests
from . import system_cmd
from pathlib import Path

system_cmd = ("python", str(system_cmd.relative_to(Path(os.getcwd()))))


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
                RoutineCommand(command="collectstatic", options={"interactive": False}),
                RoutineCommand(
                    command=("shellcompletion", "install"), switches=("import",)
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
        "import": Routine(
            commands=[
                RoutineCommand(command=("track", "2"), switches=("import", "demo")),
                RoutineCommand(
                    command=("track", "0"),
                    options={"verbosity": 0},
                    priority=1,
                    switches=("import",),
                ),
                RoutineCommand(command=("track", "3"), options={"demo": 2}, priority=3),
                RoutineCommand(
                    command=("track", "4"),
                    options={"demo": 6, "flag": True},
                    priority=3,
                ),
                RoutineCommand(command=("track", "1"), priority=4),
                RoutineCommand(command=("track", "5"), priority=6, switches=("demo",)),
                SystemCommand(
                    command=(*system_cmd, "sys 1"),
                    priority=7,
                ),
                SystemCommand(
                    command=(*system_cmd, "sys 2"),
                    priority=8,
                ),
            ],
            help_text="Test Routine 1",
            name="import",
        ),
        "--test-hyphen": Routine(
            commands=[
                RoutineCommand(
                    ("track", "1"), switches=["--hyphen-ok", "hyphen-ok-prefix"]
                ),
                RoutineCommand(("track", "2")),
                RoutineCommand(("track", "3"), switches=["hyphen-ok"]),
                RoutineCommand(("track", "4")),
                RoutineCommand(
                    ("track", "5"), switches=("hyphen-ok", "--hyphen-ok_prefix")
                ),
            ],
            help_text="Test that hyphens dont mess everything up.",
            name="--test-hyphen",
            switch_helps={
                "--hyphen-ok": "Test hyphen.",
                "--hyphen-ok-prefix": "Test hyphen with -- prefix.",
            },
        ),
        "atomic_pass": Routine(
            commands=[
                RoutineCommand(command=("edit", "0", "Name1")),
                RoutineCommand(command=("edit", "0", "Name2")),
                RoutineCommand(command=("edit", "0", "Name3")),
                RoutineCommand(command=("edit", "1", "Name4")),
            ],
            name="atomic_pass",
            help_text="Atomic test routine.",
            atomic=True,
        ),
        "atomic_fail": Routine(
            commands=[
                RoutineCommand(command=("edit", "0", "Name1")),
                RoutineCommand(command=("edit", "0", "Name2")),
                RoutineCommand(command=("edit", "0", "Name3")),
                RoutineCommand(command=("edit", "1", "Name4", "--raise")),
            ],
            name="atomic_fail",
            help_text="Atomic test routine failure.",
            atomic=True,
        ),
        "test_continue": Routine(
            commands=[
                RoutineCommand(command=("edit", "0", "Name1")),
                RoutineCommand(command=("edit", "0", "Name2", "--raise")),
                RoutineCommand(command=("edit", "0", "Name3")),
            ],
            name="test_continue",
            help_text="Test continue option.",
            continue_on_error=True,
        ),
    }
)
class SettingsAsObjectsTests(CoreTests, TestCase):
    def test_settings_format(self):
        routines = getattr(settings, ROUTINE_SETTING)
        self.assertEqual(
            routines["bad"],
            Routine(
                commands=[
                    RoutineCommand(command=("track", "0")),
                    RoutineCommand(command=("does_not_exist",)),
                    RoutineCommand(command=("track", "1")),
                ],
                help_text="Bad command test routine",
                name="bad",
            ),
        )
        self.assertEqual(
            routines["deploy"],
            Routine(
                commands=[
                    RoutineCommand(command=("makemigrations",), switches=["prepare"]),
                    RoutineCommand(command=("migrate",)),
                    RoutineCommand(command=("renderstatic",)),
                    RoutineCommand(
                        command="collectstatic", options={"interactive": False}
                    ),
                    RoutineCommand(
                        command=("shellcompletion", "install"),
                        switches=("import",),
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
        )
        self.assertEqual(
            routines["import"],
            Routine(
                commands=[
                    RoutineCommand(command=("track", "2"), switches=("import", "demo")),
                    RoutineCommand(
                        command=("track", "0"),
                        options={"verbosity": 0},
                        priority=1,
                        switches=("import",),
                    ),
                    RoutineCommand(
                        command=("track", "3"), options={"demo": 2}, priority=3
                    ),
                    RoutineCommand(
                        command=("track", "4"),
                        options={"demo": 6, "flag": True},
                        priority=3,
                    ),
                    RoutineCommand(command=("track", "1"), priority=4),
                    RoutineCommand(
                        command=("track", "5"), priority=6, switches=("demo",)
                    ),
                    SystemCommand(
                        command=(*system_cmd, "sys 1"),
                        priority=7,
                    ),
                    SystemCommand(
                        command=(*system_cmd, "sys 2"),
                        priority=8,
                    ),
                ],
                help_text="Test Routine 1",
                name="import",
            ),
        )
        self.assertEqual(
            routines["--test-hyphen"],
            Routine(
                commands=[
                    RoutineCommand(
                        ("track", "1"), switches=["hyphen_ok", "hyphen_ok_prefix"]
                    ),
                    RoutineCommand(("track", "2")),
                    RoutineCommand(("track", "3"), switches=["hyphen_ok"]),
                    RoutineCommand(("track", "4")),
                    RoutineCommand(
                        ("track", "5"), switches=("hyphen_ok", "hyphen_ok_prefix")
                    ),
                ],
                help_text="Test that hyphens dont mess everything up.",
                name="--test-hyphen",
                switch_helps={
                    "hyphen_ok": "Test hyphen.",
                    "hyphen_ok_prefix": "Test hyphen with -- prefix.",
                },
            ),
        )

        self.assertEqual(
            routines["atomic_pass"],
            Routine(
                commands=[
                    RoutineCommand(command=("edit", "0", "Name1")),
                    RoutineCommand(command=("edit", "0", "Name2")),
                    RoutineCommand(command=("edit", "0", "Name3")),
                    RoutineCommand(command=("edit", "1", "Name4")),
                ],
                name="atomic_pass",
                help_text="Atomic test routine.",
                atomic=True,
            ),
        )

        self.assertEqual(
            routines["atomic_fail"],
            Routine(
                commands=[
                    RoutineCommand(command=("edit", "0", "Name1")),
                    RoutineCommand(command=("edit", "0", "Name2")),
                    RoutineCommand(command=("edit", "0", "Name3")),
                    RoutineCommand(command=("edit", "1", "Name4", "--raise")),
                ],
                name="atomic_fail",
                help_text="Atomic test routine failure.",
                atomic=True,
            ),
        )

        self.assertEqual(
            routines["test_continue"],
            Routine(
                commands=[
                    RoutineCommand(command=("edit", "0", "Name1")),
                    RoutineCommand(command=("edit", "0", "Name2", "--raise")),
                    RoutineCommand(command=("edit", "0", "Name3")),
                ],
                name="test_continue",
                help_text="Test continue option.",
                continue_on_error=True,
            ),
        )

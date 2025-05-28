import os
from django.test import TestCase, override_settings
from django_routines import ROUTINE_SETTING, Routine, ManagementCommand, SystemCommand
from django.conf import settings
from .test_core import CoreTests
from . import system_cmd
from pathlib import Path

system_cmd = ("python", str(system_cmd.relative_to(Path(os.getcwd()))))


@override_settings(
    DJANGO_ROUTINES={
        "bad": Routine(
            commands=[
                ManagementCommand(command=("track", "0")),
                ManagementCommand(command=("does_not_exist",)),
                ManagementCommand(command=("track", "1")),
            ],
            help_text="Bad command test routine",
            name="bad",
        ),
        "deploy": Routine(
            commands=[
                ManagementCommand(command=("makemigrations",), switches=["prepare"]),
                ManagementCommand(command=("migrate",)),
                ManagementCommand(command=("renderstatic",)),
                ManagementCommand(
                    command="collectstatic", options={"interactive": False}
                ),
                ManagementCommand(
                    command=("shellcompletion", "install"), switches=("import",)
                ),
                ManagementCommand(
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
                ManagementCommand(command=("track", "2"), switches=("import", "demo")),
                ManagementCommand(
                    command=("track", "0"),
                    options={"verbosity": 0},
                    priority=1,
                    switches=("import",),
                ),
                ManagementCommand(
                    command=("track", "3"), options={"demo": 2}, priority=3
                ),
                ManagementCommand(
                    command=("track", "4"),
                    options={"demo": 6, "flag": True},
                    priority=3,
                ),
                ManagementCommand(command=("track", "1"), priority=4),
                ManagementCommand(
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
        "--test-hyphen": Routine(
            commands=[
                ManagementCommand(
                    ("track", "1"), switches=["--hyphen-ok", "hyphen-ok-prefix"]
                ),
                ManagementCommand(("track", "2")),
                ManagementCommand(("track", "3"), switches=["hyphen-ok"]),
                ManagementCommand(("track", "4")),
                ManagementCommand(
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
                ManagementCommand(command=("edit", "0", "Name1")),
                ManagementCommand(command=("edit", "0", "Name2")),
                ManagementCommand(command=("edit", "0", "Name3")),
                ManagementCommand(command=("edit", "1", "Name4")),
            ],
            name="atomic_pass",
            help_text="Atomic test routine.",
            atomic=True,
        ),
        "atomic_fail": Routine(
            commands=[
                ManagementCommand(command=("edit", "0", "Name1")),
                ManagementCommand(command=("edit", "0", "Name2")),
                ManagementCommand(command=("edit", "0", "Name3")),
                ManagementCommand(command=("edit", "1", "Name4", "--raise")),
            ],
            name="atomic_fail",
            help_text="Atomic test routine failure.",
            atomic=True,
        ),
        "test_continue": Routine(
            commands=[
                ManagementCommand(command=("edit", "0", "Name1")),
                ManagementCommand(command=("edit", "0", "Name2", "--raise")),
                ManagementCommand(command=("edit", "0", "Name3")),
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
                    ManagementCommand(command=("track", "0")),
                    ManagementCommand(command=("does_not_exist",)),
                    ManagementCommand(command=("track", "1")),
                ],
                help_text="Bad command test routine",
                name="bad",
            ),
        )
        self.assertEqual(
            routines["deploy"],
            Routine(
                commands=[
                    ManagementCommand(
                        command=("makemigrations",), switches=["prepare"]
                    ),
                    ManagementCommand(command=("migrate",)),
                    ManagementCommand(command=("renderstatic",)),
                    ManagementCommand(
                        command="collectstatic", options={"interactive": False}
                    ),
                    ManagementCommand(
                        command=("shellcompletion", "install"),
                        switches=("import",),
                    ),
                    ManagementCommand(
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
                    ManagementCommand(
                        command=("track", "2"), switches=("import", "demo")
                    ),
                    ManagementCommand(
                        command=("track", "0"),
                        options={"verbosity": 0},
                        priority=1,
                        switches=("import",),
                    ),
                    ManagementCommand(
                        command=("track", "3"), options={"demo": 2}, priority=3
                    ),
                    ManagementCommand(
                        command=("track", "4"),
                        options={"demo": 6, "flag": True},
                        priority=3,
                    ),
                    ManagementCommand(command=("track", "1"), priority=4),
                    ManagementCommand(
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
                    ManagementCommand(
                        ("track", "1"), switches=["hyphen_ok", "hyphen_ok_prefix"]
                    ),
                    ManagementCommand(("track", "2")),
                    ManagementCommand(("track", "3"), switches=["hyphen_ok"]),
                    ManagementCommand(("track", "4")),
                    ManagementCommand(
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
                    ManagementCommand(command=("edit", "0", "Name1")),
                    ManagementCommand(command=("edit", "0", "Name2")),
                    ManagementCommand(command=("edit", "0", "Name3")),
                    ManagementCommand(command=("edit", "1", "Name4")),
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
                    ManagementCommand(command=("edit", "0", "Name1")),
                    ManagementCommand(command=("edit", "0", "Name2")),
                    ManagementCommand(command=("edit", "0", "Name3")),
                    ManagementCommand(command=("edit", "1", "Name4", "--raise")),
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
                    ManagementCommand(command=("edit", "0", "Name1")),
                    ManagementCommand(command=("edit", "0", "Name2", "--raise")),
                    ManagementCommand(command=("edit", "0", "Name3")),
                ],
                name="test_continue",
                help_text="Test continue option.",
                continue_on_error=True,
            ),
        )

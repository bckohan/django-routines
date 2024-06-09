from django.test import TestCase, override_settings
from django_routines import ROUTINE_SETTING, Routine, RoutineCommand
from django.conf import settings
from .test_core import CoreTests


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
                RoutineCommand(
                    command=("track", "4"),
                    options={"demo": 6, "flag": True},
                    priority=3,
                ),
                RoutineCommand(command=("track", "1"), priority=4),
                RoutineCommand(command=("track", "5"), priority=6, switches=("demo",)),
            ],
            help_text="Test Routine 1",
            name="test",
        ),
    }
)
class SettingsAsObjectsTests(CoreTests, TestCase):
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
                            command=("track", "4"),
                            options={"demo": 6, "flag": True},
                            priority=3,
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

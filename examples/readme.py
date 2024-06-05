from . import *  # noqa: F403
from django_routines import RoutineCommand, command, routine

# register routines and their help text
routine(
    name="package",
    help_text=(
        "Generate pre-package artifacts like migrations and transpiled "
        "javascript."
    )
)
# you may register commands on a routine after defining a routine (or before!)
command("package", "makemigrations")
command("package", "renderstatic")

routine(
    "deploy",
    "Deploy the site application into production.",

    # you may also specify commands inline using the RoutineCommand dataclass
    RoutineCommand(
        ("routine", "package"), switches=["prepare"]
    ),  # routine commands can be other routines!
    RoutineCommand("migrate"),
    RoutineCommand("collectstatic"),
    RoutineCommand(("shellcompletion", "install"), switches=["initial"]),
    RoutineCommand(("loaddata", "./fixtures/demo.json"), switches=["demo"]),

    # define switches that toggle commands on and off
    prepare="Generate artifacts like migrations and transpiled javascript.",
    initial="Things to do on the very first deployment on a new server.",
    demo="Load the demo data.",
)

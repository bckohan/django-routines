from . import *  # noqa: F4093
from django_routines import (
    ManagementCommand,
    SystemCommand,
    command,
    system,
    routine
)

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
system("package", "poetry", "build")

routine(
    "deploy",
    "Deploy the site application into production.",

    # you may also specify commands inline using the ManagementCommand dataclass
    ManagementCommand(
        ("routine", "package"), switches=["prepare"]
    ),  # routine commands can be other routines!
    ManagementCommand("migrate"),
    ManagementCommand("collectstatic"),
    ManagementCommand(("shellcompletion", "install"), switches=["initial"]),
    ManagementCommand(("loaddata", "./fixtures/demo.json"), switches=["demo"]),
    SystemCommand(("touch", "/path/to/wsgi.py")),

    # define switches that toggle commands on and off
    prepare="Generate artifacts like migrations and transpiled javascript.",
    initial="Things to do on the very first deployment on a new server.",
    demo="Load the demo data.",
)

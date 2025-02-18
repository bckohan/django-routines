import os
from pathlib import Path
from django_routines import (
    routine,
    command,
    system,
    Routine,
    RoutineCommand,
    SystemCommand,
    get_routine,
    routines,
)
from tests import track_file, system_cmd
from django.utils.translation import gettext_lazy as _
from tests.base_settings import *

track_file = str(track_file.relative_to(Path(os.getcwd())))
system_cmd = ("python", str(system_cmd.relative_to(Path(os.getcwd()))))

USE_TZ = True


# Set default terminal width for help outputs - necessary for
# testing help output in CI environments.
os.environ["TERMINAL_WIDTH"] = "80"

routine(
    "deploy",
    _("Deploy the site application into production."),
    RoutineCommand(("makemigrations",), switches=["prepare"]),
    RoutineCommand(("migrate",)),
    RoutineCommand(("renderstatic",)),
    RoutineCommand("collectstatic", options={"interactive": False}),
    prepare=_("Prepare the deployment."),
    demo="Deploy the demo.",
)

command("deploy", "shellcompletion", "install", switches=["import"])
command("deploy", "loaddata", "./fixtures/initial_data.json", switches=["demo"])

assert get_routine("deploy").name == "deploy"


command("import", "track", "2", priority=0, switches=("import", "demo"))
routine(
    "import",
    _("Test Routine 1"),
    RoutineCommand(
        ("track", "0"), priority=1, switches=("import",), options={"verbosity": 0}
    ),
    RoutineCommand(("track", "1"), priority=4),
    SystemCommand((*system_cmd, "sys 2"), priority=8),
)

command("import", "track", "3", priority=3, demo=2)
command("import", "track", "4", priority=3, demo=6, flag=True)
command("import", "track", "5", priority=6, switches=["demo"])
system("import", *system_cmd, "sys 1", priority=7)


names = set()
for rtn in routines():
    assert isinstance(rtn, Routine)
    names.add(rtn.name)

assert names == {"deploy", "import"}

routine(
    "bad",
    _("Bad command test routine"),
    RoutineCommand(("track", "0")),
    RoutineCommand(("does_not_exist",)),
    RoutineCommand(("track", "1")),
)

routine(
    "--test-hyphen",
    "Test that hyphens dont mess everything up.",
    RoutineCommand(("track", "1"), switches=["--hyphen-ok", "hyphen-ok-prefix"]),
    RoutineCommand(("track", "2")),
    RoutineCommand(("track", "3"), switches=["hyphen-ok"]),
    RoutineCommand(("track", "4")),
    RoutineCommand(("track", "5"), switches=("hyphen-ok", "--hyphen-ok_prefix")),
    hyphen_ok="Test hyphen.",
    hyphen_ok_prefix="Test hyphen with -- prefix.",
)

routine(
    "atomic_pass",
    "Atomic test routine.",
    RoutineCommand(command=("edit", "0", "Name1")),
    RoutineCommand(command=("edit", "0", "Name2")),
    RoutineCommand(command=("edit", "0", "Name3")),
    RoutineCommand(command=("edit", "1", "Name4")),
    atomic=True,
)

routine(
    "atomic_fail",
    "Atomic test routine failure.",
    RoutineCommand(command=("edit", "0", "Name1")),
    RoutineCommand(command=("edit", "0", "Name2")),
    RoutineCommand(command=("edit", "0", "Name3")),
    RoutineCommand(command=("edit", "1", "Name4", "--raise")),
    atomic=True,
)

routine(
    "test_continue",
    "Test continue option.",
    RoutineCommand(command=("edit", "0", "Name1")),
    RoutineCommand(command=("edit", "0", "Name2", "--raise")),
    RoutineCommand(command=("edit", "0", "Name3")),
    continue_on_error=True,
)

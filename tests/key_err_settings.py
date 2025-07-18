from django_routines import Routine, ManagementCommand
from .base_settings import *


DJANGO_ROUTINES = {
    "keyerr-bug": Routine(
        commands=[
            ManagementCommand(command=("keyerr",)),
        ],
        help_text=("Test the KeyError exception bug."),
        name="keyerr-bug",
    ),
}

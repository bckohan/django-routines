from .base_settings import *
from django_routines import routine, RoutineCommand


routine(
    "subproc_opt_error",
    "Test what happens when you can't convert an option to subprocess arg string.",
    RoutineCommand(("collectstatic"), options={"not-an-option": False}),
)

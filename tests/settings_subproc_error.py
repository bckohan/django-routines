from .base_settings import *
from django_routines import routine, SystemCommand


routine(
    "subproc_error",
    "Test what happens when a subprocess throws an error.",
    SystemCommand(("python", "tests/throw_error.py")),
)

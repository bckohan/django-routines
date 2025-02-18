from .base_settings import *
from django_routines import routine, RoutineCommand


routine(
    "option-on",
    "Test what happens when supplied command option is toggled on.",
    RoutineCommand("collectstatic", options={"interactive": False}),
)

routine(
    "option-off",
    "Test what happens when supplied command option is toggled off.",
    RoutineCommand("collectstatic", options={"interactive": True}),
)

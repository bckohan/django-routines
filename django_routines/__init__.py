r"""

    ____    _                            ____              __  _
   / __ \  (_)___ _____  ____ _____     / __ \____  __  __/ /_(_)___  ___  _____
  / / / / / / __ `/ __ \/ __ `/ __ \   / /_/ / __ \/ / / / __/ / __ \/ _ \/ ___/
 / /_/ / / / /_/ / / / / /_/ / /_/ /  / _, _/ /_/ / /_/ / /_/ / / / /  __(__  )
/_____/_/ /\__,_/_/ /_/\__, /\____/  /_/ |_|\____/\__,_/\__/_/_/ /_/\___/____/
     /___/            /____/



"""

import bisect
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, cast

VERSION = (1, 0, 0)

__title__ = "Django Routines"
__version__ = ".".join(str(i) for i in VERSION)
__author__ = "Brian Kohan"
__license__ = "MIT"
__copyright__ = "Copyright 2024 Brian Kohan"


ROUTINE_SETTING = "ROUTINES"


@dataclass
class RoutineCommand:
    """
    Dataclass to hold the routine command information.
    """

    command: Tuple[str, ...]
    """
    The command and its arguments to run the routine, all strings or
    coercible to strings that the command will parse correctly.
    """

    priority: int = 0
    """
    The order of the command in the routine. Priority ties will be run in
    insertion order.
    """

    switches: Tuple[str, ...] = tuple()
    """
    The command will run only when one of these switches is active,
    or for all invocations of the routine if no switches are configured.
    """

    options: Dict[str, Any] = field(default_factory=dict)
    """
    Any options to pass to the command via call_command.
    """


@dataclass
class Routine:
    """
    Dataclass to hold the routine information.
    """

    name: str
    """
    The name of the routine.
    """

    help_text: str
    """
    The help text to display for the routine.
    """

    commands: List[RoutineCommand] = field(default_factory=list)
    """
    The commands to run in the routine.
    """

    switch_helps: Dict[str, str] = field(default_factory=dict)

    def __len__(self):
        return len(self.commands)

    @property
    def switches(self) -> Set[str]:
        switches: Set[str] = set()
        for command in self.commands:
            if command.switches:
                switches.update(command.switches)
        return switches

    def plan(self, switches: Set[str]) -> List[RoutineCommand]:
        return [
            command
            for command in self.commands
            if not command.switches
            or any(switch in switches for switch in command.switches)
        ]

    def command(self, command: RoutineCommand):
        bisect.insort(self.commands, command, key=lambda cmd: cmd.priority)
        return command


def get_routine(name: str) -> Routine:
    """
    Get the routine by name.

    .. note::

        If called before settings have been configured, this function must be called from settings.

    :param name: The name of the routine to get.
    :return: The routine.
    :raises: KeyError if the routine does not exist, or routines have not been
        configured.
    """
    from django.conf import settings

    if not settings.configured:
        return sys._getframe(1).f_globals[ROUTINE_SETTING][name]  # noqa: WPS437
    return getattr(settings, ROUTINE_SETTING, {})[name]


def routine(name: str, help_text: str = "", *commands: RoutineCommand, **switch_helps):
    """
    Register a routine to the list of routines in settings to be run.

    :param name: The name of the routine to register.
    :param help_text: The help text to display for the routine by the routines command.
    :param commands: The commands to run in the routine.
    """
    settings = sys._getframe(1).f_globals  # noqa: WPS437
    settings.setdefault(ROUTINE_SETTING, {})
    routine = Routine(name, help_text, switch_helps=switch_helps)
    for command in commands:
        routine.command(command)
    settings[ROUTINE_SETTING][name] = routine


def command(
    routine: str,
    *command: str,
    priority: int = RoutineCommand.priority,
    switches: Optional[Sequence[str]] = RoutineCommand.switches,
    **options,
):
    """
    Add a routine to the list of routines in settings to be run.

    .. note::

        You must call this function from a settings file.

    :param routine: The name of the routine the command belongs to.
    :param command: The command and its arguments to run the routine, all strings or
        coercible to strings that the command will parse correctly.
    :param priority: The order of the command in the routine. Priority ties will be run in
        insertion order.
    :param switches: The command will run only when one of these switches is active,
        or for all invocations of the routine if no switches are configured.
    :param options: Any options to pass to the command via call_command.
    :return: The new command.
    """
    settings = sys._getframe(1).f_globals  # noqa: WPS437
    settings.setdefault(ROUTINE_SETTING, {})
    settings[ROUTINE_SETTING].setdefault(routine, Routine(routine, "", []))
    return settings[ROUTINE_SETTING][routine].command(
        RoutineCommand(
            cast(Tuple[str], command), priority, tuple(switches or []), options
        )
    )

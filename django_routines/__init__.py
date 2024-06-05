r"""
::

        ____    _                            ____              __  _
       / __ \  (_)___ _____  ____ _____     / __ \____  __  __/ /_(_)___  ___  _____
      / / / / / / __ `/ __ \/ __ `/ __ \   / /_/ / __ \/ / / / __/ / __ \/ _ \/ ___/
     / /_/ / / / /_/ / / / / /_/ / /_/ /  / _, _/ /_/ / /_/ / /_/ / / / /  __(__  )
    /_____/_/ /\__,_/_/ /_/\__, /\____/  /_/ |_|\____/\__,_/\__/_/_/ /_/\___/____/
         /___/            /____/


A simple Django app that allows you to specify batches of commands in your settings files
and then run them in sequence by name using the provied ``routine`` command.
"""

import bisect
import sys
import typing as t
from dataclasses import asdict, dataclass, field

from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import Promise

VERSION = (1, 0, 0)

__title__ = "Django Routines"
__version__ = ".".join(str(i) for i in VERSION)
__author__ = "Brian Kohan"
__license__ = "MIT"
__copyright__ = "Copyright 2024 Brian Kohan"

__all__ = [
    "ROUTINE_SETTING",
    "RoutineCommand",
    "Routine",
    "routine",
    "command",
    "get_routine",
    "routines",
]


ROUTINE_SETTING = "DJANGO_ROUTINES"


R = t.TypeVar("R")


@dataclass
class RoutineCommand:
    """
    Dataclass to hold the routine command information.
    """

    command: t.Union[str, t.Tuple[str, ...]]
    """
    The command and its arguments to run the routine, all strings or
    coercible to strings that the command will parse correctly.
    """

    priority: int = 0
    """
    The order of the command in the routine. Priority ties will be run in
    insertion order.
    """

    switches: t.Tuple[str, ...] = tuple()
    """
    The command will run only when one of these switches is active,
    or for all invocations of the routine if no switches are configured.
    """

    options: t.Dict[str, t.Any] = field(default_factory=dict)
    """
    t.Any options to pass to the command via call_command.
    """

    @property
    def command_name(self) -> str:
        return self.command if isinstance(self.command, str) else self.command[0]

    @property
    def command_args(self) -> t.Tuple[str, ...]:
        return tuple() if isinstance(self.command, str) else self.command[1:]

    @property
    def command_str(self) -> str:
        return self.command if isinstance(self.command, str) else " ".join(self.command)

    @classmethod
    def from_dict(
        cls, obj: t.Union["RoutineCommand", t.Dict[str, t.Any]]
    ) -> "RoutineCommand":
        """
        Return a RoutineCommand object from a dictionary representing it.
        """
        return obj if isinstance(obj, RoutineCommand) else RoutineCommand(**obj)


def _insort_right_with_key(a: t.List[R], x: R, key: t.Callable[[R], t.Any]) -> None:
    """
    A function that implements bisect.insort_right with a key callable on items.

    todo: remove this and replace with key argument to bisect.insort_right when support for
    python <3.10 dropped.
    """
    transformed_list = [key(item) for item in a]
    transformed_x = key(x)
    insert_point = bisect.bisect_right(transformed_list, transformed_x)
    a.insert(insert_point, x)


@dataclass
class Routine:
    """
    Dataclass to hold the routine information.
    """

    name: str
    """
    The name of the routine.
    """

    help_text: t.Union[str, Promise]
    """
    The help text to display for the routine.
    """

    commands: t.List[RoutineCommand] = field(default_factory=list)
    """
    The commands to run in the routine.
    """

    switch_helps: t.Dict[str, t.Union[str, Promise]] = field(default_factory=dict)

    def __len__(self):
        return len(self.commands)

    @property
    def switches(self) -> t.List[str]:
        switches: t.Set[str] = set()
        for command in self.commands:
            if command.switches:
                switches.update(command.switches)
        return sorted(switches)

    def plan(self, switches: t.Set[str]) -> t.List[RoutineCommand]:
        return [
            command
            for command in self.commands
            if not command.switches
            or any(switch in switches for switch in command.switches)
        ]

    def add(self, command: RoutineCommand):
        # python >= 3.10
        # bisect.insort(self.commands, command, key=lambda cmd: cmd.priority)
        _insort_right_with_key(
            self.commands, command, key=lambda cmd: cmd.priority or 0
        )
        return command

    @classmethod
    def from_dict(cls, obj: t.Union["Routine", t.Dict[str, t.Any]]) -> "Routine":
        """
        Return a RoutineCommand object from a dictionary representing it.
        """
        if isinstance(obj, Routine):
            return obj
        return Routine(
            **{attr: val for attr, val in obj.items() if attr != "commands"},
            commands=[RoutineCommand.from_dict(cmd) for cmd in obj.get("commands", [])],
        )


def routine(
    name: str,
    help_text: t.Union[str, Promise] = "",
    *commands: RoutineCommand,
    **switch_helps,
):
    """
    Register a routine to the t.List of routines in settings to be run.

    :param name: The name of the routine to register.
    :param help_text: The help text to display for the routine by the routines command.
    :param commands: The commands to run in the routine.
    """
    settings = sys._getframe(1).f_globals  # noqa: WPS437
    if not settings.get(ROUTINE_SETTING, {}):
        settings[ROUTINE_SETTING] = {}

    existing: t.List[RoutineCommand] = []
    try:
        routine = get_routine(name)
        help_text = (
            help_text
            # don't trigger translation - we're in settings!
            if isinstance(help_text, Promise) or help_text
            else routine.help_text
        )
        switch_helps = {**routine.switch_helps, **switch_helps}
        existing = routine.commands
    except KeyError:
        pass
    routine = Routine(
        name, help_text=help_text, commands=existing, switch_helps=switch_helps
    )

    for command in commands:
        routine.add(command)
    settings[ROUTINE_SETTING][name] = asdict(routine)


def command(
    routine: str,
    *command: str,
    priority: int = RoutineCommand.priority,
    switches: t.Optional[t.Sequence[str]] = RoutineCommand.switches,
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
        insertion order (defaults to zero).
    :param switches: The command will run only when one of these switches is active,
        or for all invocations of the routine if no switches are configured.
    :param options: t.Any options to pass to the command via call_command.
    :return: The new command.
    """
    settings = sys._getframe(1).f_globals  # noqa: WPS437
    settings[ROUTINE_SETTING] = settings.get(ROUTINE_SETTING, {}) or {}
    routine_dict = settings[ROUTINE_SETTING]
    routine_obj = (
        Routine.from_dict(routine_dict[routine])
        if routine in routine_dict
        else Routine(routine, "", [])
    )
    new_cmd = routine_obj.add(
        RoutineCommand(
            t.cast(t.Tuple[str], command), priority, tuple(switches or []), options
        )
    )
    routine_dict[routine] = asdict(routine_obj)
    return new_cmd


def get_routine(name: str) -> Routine:
    """
    Get the routine by name.

    .. note::

        If called before settings have been configured, this function must be called from settings.

    :param name: The name of the routine to get.
    :return: The routine.
    :raises: KeyError if the routine does not exist, or routines have not been
        configured.
    :raises: ImproperlyConfigured if the DJANGO_ROUTINES settings variable is not valid.
    """
    from django.conf import settings

    try:
        if not settings.configured:
            Routine.from_dict(sys._getframe(1).f_globals.get(ROUTINE_SETTING, {})[name])  # noqa: WPS437
        return Routine.from_dict(getattr(settings, ROUTINE_SETTING, {})[name])
    except TypeError as err:
        raise ImproperlyConfigured(
            f"{ROUTINE_SETTING} routine {name} is malformed."
        ) from err


def routines() -> t.Generator[Routine, None, None]:
    """
    A generator that yields Routine objects from settings.
    :yield: Routine objects
    :raises: ImproperlyConfigured if the DJANGO_ROUTINES settings variable is not valid.
    """
    from django.conf import settings

    routines = (
        sys._getframe(1).f_globals.get(ROUTINE_SETTING, {})  # noqa: WPS437
        if not settings.configured
        else getattr(settings, ROUTINE_SETTING, {})
    ) or {}
    for name, routine in routines.items():
        try:
            yield Routine.from_dict(routine)
        except TypeError as err:
            raise ImproperlyConfigured(
                f"{ROUTINE_SETTING} routine {name} is malformed."
            ) from err

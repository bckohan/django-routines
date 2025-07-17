r"""
::

        ██████╗      ██╗ █████╗ ███╗   ██╗ ██████╗  ██████╗
        ██╔══██╗     ██║██╔══██╗████╗  ██║██╔════╝ ██╔═══██╗
        ██║  ██║     ██║███████║██╔██╗ ██║██║  ███╗██║   ██║
        ██║  ██║██   ██║██╔══██║██║╚██╗██║██║   ██║██║   ██║
        ██████╔╝╚█████╔╝██║  ██║██║ ╚████║╚██████╔╝╚██████╔╝
        ╚═════╝  ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝  ╚═════╝

    ██████╗  ██████╗ ██╗   ██╗████████╗██╗███╗   ██╗███████╗███████╗
    ██╔══██╗██╔═══██╗██║   ██║╚══██╔══╝██║████╗  ██║██╔════╝██╔════╝
    ██████╔╝██║   ██║██║   ██║   ██║   ██║██╔██╗ ██║█████╗  ███████╗
    ██╔══██╗██║   ██║██║   ██║   ██║   ██║██║╚██╗██║██╔══╝  ╚════██║
    ██║  ██║╚██████╔╝╚██████╔╝   ██║   ██║██║ ╚████║███████╗███████║
    ╚═╝  ╚═╝ ╚═════╝  ╚═════╝    ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝


A simple Django app that allows you to specify batches of commands in your settings
files and then run them in sequence by name using the provided ``routine`` command.
"""

import bisect
import keyword
import sys
import typing as t
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field

from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import Promise

VERSION = (1, 5, 1)

__title__ = "Django Routines"
__version__ = ".".join(str(i) for i in VERSION)
__author__ = "Brian Kohan"
__license__ = "MIT"
__copyright__ = "Copyright 2024-2025 Brian Kohan"

__all__ = [
    "ROUTINE_SETTING",
    "ManagementCommand",
    "SystemCommand",
    "Routine",
    "routine",
    "command",
    "get_routine",
    "routines",
    "Command",
    "PreHook",
    "PostHook",
]


ROUTINE_SETTING = "DJANGO_ROUTINES"


R = t.TypeVar("R")
CommandTypes = t.Union[t.Type["ManagementCommand"], t.Type["SystemCommand"]]
Command = t.Union["ManagementCommand", "SystemCommand"]
"""
Command type, either a ManagementCommand or SystemCommand.
"""

_Hook = t.Callable[
    [
        "Routine",
        "Command",
        t.Optional["Command"],
        t.Dict[str, t.Any],
    ],
    t.Optional[bool],
]

PreHook = _Hook
"""
Function type signature for a pre-hook functions. Pre-hook functions can modify command
objects (including their arguments) before they are run.

:param routine: The routine being run.
:param command: The command about to be run.
:param previous: The previous command that was run (or None if at the beginning).
:param options: A dictionary containing the routine level options.
:return: Return true to skip the command.
"""

PostHook = _Hook
"""
Function type signature for a post-hook functions. Post-hook functions can modify
command objects (including their results) after they are run or the next command
before it is run. Returning a truthy value will exit the routine early.

:param routine: The routine being run.
:param command: The command about to be run.
:param next: The next command that will be run (or None if at the end).
:param options: A dictionary containing the routine level options.
:return: Return true to exit the routine early.
"""


def to_symbol(name: str, check_keyword: bool = False) -> str:
    symbol = name.lstrip("-").replace("-", "_")
    if check_keyword and symbol.lower() in keyword.kwlist:
        return f"{symbol}_"
    return symbol


def to_cli_option(name: str) -> str:
    return f"--{to_symbol(name, check_keyword=False).replace('_', '-')}"


@dataclass
class _RoutineCommand(ABC):
    """
    A base Dataclass to hold the routine command information.
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

    switches: t.Union[t.List[str], t.Tuple[str, ...]] = tuple()
    """
    The command will run only when one of these switches is active,
    or for all invocations of the routine if no switches are configured.
    """

    pre_hook: t.Optional[PreHook] = None
    """
    A function that will be run before the command is run. It may make modifications
    to the command or decide to skip the command by returning True. See :attr:`PreHook`
    """

    post_hook: t.Optional[PostHook] = None
    """
    A function that will be run after the command has been run. It may make
    modifications to the command (including its result) or decide to exit the routine
    early by returning True. See :attr:`PostHook`

    It may also make modifications to the next command that will be run, if any.
    """

    result: t.Any = None
    """
    The result of the command run. This will either be the value returned by
    :func:`~django.core.management.call_command` or a :func:`subprocess.run` result
    object if the command was run in a subprocess.
    """

    def __post_init__(self):
        self.switches = tuple([to_symbol(switch) for switch in self.switches])

    @property
    @abstractmethod
    def kind(self) -> str:
        """The kind of this command (i.e. management or system)."""

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
        cls,
        obj: t.Union[Command, t.Dict[str, t.Any]],
    ) -> Command:
        """
        Return a RoutineCommand object from a dictionary representing it.
        """
        if isinstance(obj, dict):
            cmd_cls: CommandTypes = ManagementCommand
            if obj.get("kind", None) == "system":
                cmd_cls = SystemCommand
            return cmd_cls(**{k: v for k, v in obj.items() if k != "kind"})
        return obj

    def to_dict(self) -> t.Dict[str, t.Any]:
        return {**asdict(self), "kind": self.kind}


@dataclass
class ManagementCommand(_RoutineCommand):
    options: t.Dict[str, t.Any] = field(default_factory=dict)
    """
    Any options to pass to the command via
    :func:`~django.core.management.call_command`. Not valid for SystemCommands
    """

    @property
    def kind(self) -> str:
        return "management"


# this alias is for backwards compat and will be removed in 2.0
RoutineCommand = ManagementCommand


@dataclass
class SystemCommand(_RoutineCommand):
    """
    A RoutineCommand that represents a system command instead of a management command.
    """

    @property
    def kind(self) -> str:
        return "system"


def _insort_right_with_key(a: t.List[R], x: R, key: t.Callable[[R], t.Any]) -> None:
    """
    A function that implements bisect.insort_right with a key callable on items.

    todo: remove this and replace with key argument to bisect.insort_right when support
    for python <3.10 dropped.
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

    commands: t.List[Command] = field(default_factory=list)
    """
    The commands to run in the routine.
    """

    switch_helps: t.Dict[str, t.Union[str, Promise]] = field(default_factory=dict)

    subprocess: bool = False
    """
    If true run each of the commands in a subprocess.
    """

    atomic: bool = False
    """
    Run all commands in the same transaction.
    """

    continue_on_error: bool = False
    """
    Keep going if a command fails.
    """

    pre_hook: t.Optional[PreHook] = None
    """
    This function will be run before each command that lacks its own pre_hook in the
    routine. See :attr:`PreHook`. You can determine if this is the starting command
    of the routine by checking if the previous command is None.
    """

    post_hook: t.Optional[PostHook] = None
    """
    This function will be run after each command that lacks its own post_hook in the
    routine. See :attr:`PostHook`. You can determine if this is the last command of the
    routine by checking if the next command is None. Post hooks may also be used to
    exit the routine early by returning True.
    """

    def __post_init__(self):
        self.name = to_symbol(self.name)
        self.switch_helps = {
            to_symbol(switch): hlp for switch, hlp in self.switch_helps.items()
        }

    def __len__(self):
        return len(self.commands)

    @property
    def switches(self) -> t.List[str]:
        switches: t.Set[str] = set()
        for command in self.commands:
            if command.switches:
                switches.update(command.switches)
        return sorted(switches)

    def plan(self, switches: t.Set[str]) -> t.List[Command]:
        def set_hooks(
            command: Command,
            pre_hook: t.Optional[PreHook],
            post_hook: t.Optional[PostHook],
        ) -> Command:
            if pre_hook and not command.pre_hook:
                command.pre_hook = pre_hook
            if post_hook and not command.post_hook:
                command.post_hook = post_hook
            return command

        return [
            set_hooks(command, self.pre_hook, self.post_hook)
            for command in self.commands
            if not command.switches
            or any(switch in switches for switch in command.switches)
        ]

    def add(self, command: Command):
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
        commands: t.List[Command] = []
        for cmd in obj.get("commands", []):
            _insort_right_with_key(
                commands,
                _RoutineCommand.from_dict(cmd),
                key=lambda cmd: cmd.priority or 0,
            )
        return Routine(
            **{attr: val for attr, val in obj.items() if attr != "commands"},
            commands=commands,
        )

    def to_dict(self) -> t.Dict[str, t.Any]:
        return {
            "name": self.name,
            "help_text": self.help_text,
            "commands": [cmd.to_dict() for cmd in self.commands],
            "switch_helps": self.switch_helps,
            "subprocess": self.subprocess,
            "atomic": self.atomic,
            "continue_on_error": self.continue_on_error,
            "pre_hook": self.pre_hook,
            "post_hook": self.post_hook,
        }


def routine(
    name: str,
    help_text: t.Union[str, Promise] = "",
    *commands: Command,
    subprocess: bool = False,
    atomic: bool = False,
    continue_on_error: bool = False,
    pre_hook: t.Optional[PreHook] = None,
    post_hook: t.Optional[PostHook] = None,
    **switch_helps,
):
    """
    Register a routine to the t.List of routines in settings to be run.

    :param name: The name of the routine to register.
    :param help_text: The help text to display for the routine by the routines command.
    :param commands: The commands to run in the routine.
    :param subprocess: If true run each of the commands in a subprocess.
    :param atomic: Run all commands in the same transaction.
    :param continue_on_error: Keep going if a command fails.
    :param pre_hook: A function to run before each command in the routine is run if the
        command does not have its own pre_hook. See :attr:`PreHook`
    :param post_hook: A function to run after each command in the routine is run if the
        command does not have its own post_hook. See :attr:`PostHook`
    :param switch_helps: A mapping of switch names to help text for the switches.
    :raises: ImproperlyConfigured if the DJANGO_ROUTINES settings variable is not valid.
    """
    settings = sys._getframe(1).f_globals
    if not settings.get(ROUTINE_SETTING, {}):
        settings[ROUTINE_SETTING] = {}

    existing: t.List[Command] = []
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
        name,
        help_text=help_text,
        commands=existing,
        switch_helps=switch_helps,
        subprocess=subprocess,
        atomic=atomic,
        continue_on_error=continue_on_error,
        pre_hook=pre_hook,
        post_hook=post_hook,
    )

    for command in commands:
        routine.add(command)

    settings[ROUTINE_SETTING][routine.name] = routine.to_dict()


def _get_routine(routine_name: str, routines: t.Dict[str, t.Any]) -> Routine:
    """
    Routine may undergo some normalization, we account for that here when trying
    to fetch them.
    """
    try:
        routine_name = to_symbol(routine_name)
        return routines[routine_name]
    except KeyError:
        for name, routine in routines.items():
            if to_symbol(name).lower() == routine_name.lower():
                return routine
        raise


def _add_command(
    command_type: CommandTypes,
    routine: str,
    *command: str,
    priority: int = _RoutineCommand.priority,
    switches: t.Optional[t.Sequence[str]] = _RoutineCommand.switches,
    pre_hook: t.Optional[PreHook] = None,
    post_hook: t.Optional[PostHook] = None,
    **options,
):
    settings = sys._getframe(2).f_globals
    settings[ROUTINE_SETTING] = settings.get(ROUTINE_SETTING, {}) or {}
    routine_dict = settings[ROUTINE_SETTING]
    try:
        routine_obj = Routine.from_dict(_get_routine(routine, routine_dict))
    except KeyError:
        routine_obj = Routine(routine, "", [])
    extra = {"options": options} if command_type is ManagementCommand else {}
    new_cmd = routine_obj.add(
        command_type(
            t.cast(t.Tuple[str], command),
            priority,
            tuple(switches or []),
            pre_hook=pre_hook,
            post_hook=post_hook,
            **extra,
        )
    )
    routine_dict[routine] = routine_obj.to_dict()
    return new_cmd


def command(
    routine: str,
    *command: str,
    priority: int = RoutineCommand.priority,
    switches: t.Optional[t.Sequence[str]] = RoutineCommand.switches,
    pre_hook: t.Optional[PreHook] = None,
    post_hook: t.Optional[PostHook] = None,
    **options,
):
    """
    Add a command to the named routine in settings to be run.

    .. note::

        You must call this function from a settings file.

    :param routine: The name of the routine the command belongs to.
    :param command: The command and its arguments to run the routine, all strings or
        coercible to strings that the command will parse correctly.
    :param priority: The order of the command in the routine. Priority ties will be run in
        insertion order (defaults to zero).
    :param switches: The command will run only when one of these switches is active,
        or for all invocations of the routine if no switches are configured.
    :param options: t.Any options to pass to the command via
        :func:`~django.core.management.call_command`.
    :param pre_hook: A function to run before the command is run. See :attr:`PreHook`
    :param post_hook: A function to run after the command has been run. See
        :attr:`PostHook`
    :raises: ImproperlyConfigured if the DJANGO_ROUTINES settings variable is not valid.
    :return: The new command.
    """
    return _add_command(
        ManagementCommand,
        routine,
        *command,
        priority=priority,
        switches=switches,
        pre_hook=pre_hook,
        post_hook=post_hook,
        **options,
    )


def system(
    routine: str,
    *command: str,
    priority: int = _RoutineCommand.priority,
    switches: t.Optional[t.Sequence[str]] = _RoutineCommand.switches,
    pre_hook: t.Optional[PreHook] = None,
    post_hook: t.Optional[PostHook] = None,
):
    """
    Add a system command to the named routine in settings to be run.

    .. note::

        You must call this function from a settings file.

    :param routine: The name of the routine the command belongs to.
    :param command: The command and its arguments to run the routine, all strings or
        coercible to strings that the command will parse correctly.
    :param priority: The order of the command in the routine. Priority ties will be run
        in insertion order (defaults to zero).
    :param switches: The command will run only when one of these switches is active,
        or for all invocations of the routine if no switches are configured.
    :param pre_hook: A function to run before the command is run. See :attr:`PreHook`
    :param post_hook: A function to run after the command has been run. See
        :attr:`PostHook`
    :raises: ImproperlyConfigured if the DJANGO_ROUTINES settings variable is not valid.
    :return: The new command.
    """
    return _add_command(
        SystemCommand,
        routine,
        *command,
        priority=priority,
        switches=switches,
        pre_hook=pre_hook,
        post_hook=post_hook,
    )


def get_routine(name: str) -> Routine:
    """
    Get the routine by name.

    .. note::

        If called before settings have been configured, this function must be called
        from settings.

    :param name: The name of the routine to get.
    :return: The routine.
    :raises: KeyError if the routine does not exist, or routines have not been
        configured.
    :raises: ImproperlyConfigured if the DJANGO_ROUTINES settings variable is not valid.
    """
    from django.conf import settings

    try:
        if not settings.configured:
            Routine.from_dict(
                _get_routine(name, sys._getframe(1).f_globals.get(ROUTINE_SETTING, {}))
            )
        return Routine.from_dict(
            _get_routine(name, getattr(settings, ROUTINE_SETTING, {}))
        )
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
        sys._getframe(1).f_globals.get(ROUTINE_SETTING, {})
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

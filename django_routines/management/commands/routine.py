import typing as t
from importlib.util import find_spec

import click
import typer
from django.core.management import CommandError, call_command
from django.core.management.base import BaseCommand
from django.utils.translation import gettext as _
from django_typer import TyperCommand, get_command, initialize
from django_typer.types import Verbosity

from django_routines import (
    Routine,
    RoutineCommand,
    get_routine,
    routines,
)

width = 80
use_rich = find_spec("rich") is not None
if use_rich:
    from rich.console import Console

    width = Console().width


COMMAND_TMPL = """
import sys
if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

def {routine}(
    self,
    context: typer.Context,
    all: Annotated[bool, typer.Option("--all", help="{all_help}")] = False,
    {switch_args}
):
    self.routine = "{routine}"
    self.switches = []
    {add_switches}
    if not context.invoked_subcommand:
        return self._run_routine()
    return self.{routine}
"""


class Command(TyperCommand, rich_markup_mode="rich"):  # type: ignore
    """
    A TyperCommand_
    """

    help = _("Run batches of commands configured in settings.")

    verbosity: int = 1
    switches: t.Set[str] = set()

    suppressed_base_arguments = set()

    _routine: t.Optional[Routine] = None
    _verbosity_passed: bool = False

    @property
    def routine(self) -> t.Optional[Routine]:
        return self._routine

    @routine.setter
    def routine(self, routine: t.Union[str, Routine]):
        self._routine = (
            routine if isinstance(routine, Routine) else get_routine(str(routine))
        )

    @property
    def plan(self) -> t.List[RoutineCommand]:
        assert self.routine
        return self.routine.plan(self.switches)

    @initialize()
    def init(self, ctx: typer.Context, verbosity: Verbosity = verbosity):
        self.verbosity = verbosity
        self._pass_verbosity = (
            ctx.get_parameter_source("verbosity")
            is not click.core.ParameterSource.DEFAULT
        )

    def _run_routine(self):
        assert self.routine
        for command in self.plan:
            if self.verbosity > 0:
                self.secho(command.command_str, fg="cyan")
            try:
                cmd = get_command(
                    command.command_name,
                    BaseCommand,
                    stdout=t.cast(t.IO[str], self.stdout._out),
                    stderr=t.cast(t.IO[str], self.stderr._out),
                    force_color=self.force_color,
                    no_color=self.no_color,
                )
                options = command.options
                if (
                    self._pass_verbosity
                    and not any(
                        "verbosity" in arg
                        for arg in getattr(cmd, "suppressed_base_arguments", [])
                    )
                    and not any("--verbosity" in arg for arg in command.command_args)
                ):
                    # only pass verbosity if it was passed to routines, not suppressed
                    # by the command class and not passed by the configured command
                    options = {"verbosity": self.verbosity, **options}
                call_command(cmd, *command.command_args, **options)
            except KeyError:
                raise CommandError(f"Command not found: {command.command_name}")

    def _list(self) -> None:
        for command in self.plan:
            priority = str(command.priority)
            cmd_str = command.command_str
            switches_str = " | " if command.switches else ""
            opt_str = " ".join([f"{k}={v}" for k, v in command.options.items()])
            if self.force_color or not self.no_color:
                priority = click.style(priority, fg="green")
                cmd_str = click.style(cmd_str, fg="cyan", bold=True)
                opt_str = " ".join(
                    [
                        f"{click.style(k, 'blue')}={click.style(v, 'magenta')}"
                        for k, v in command.options.items()
                    ]
                )
                switches_str += ", ".join(
                    click.style(switch, fg="yellow")
                    for switch in (command.switches or [])
                )
            else:
                switches_str += ", ".join(command.switches or [])

            opt_str = f" ({opt_str})" if opt_str else ""
            self.secho(f"[{priority}] {cmd_str}{opt_str}{switches_str}")


for routine in routines():
    switches = routine.switches
    switch_args = ", ".join(
        [
            f"{switch}: Annotated[bool, typer.Option('--{switch}', help='{routine.switch_helps.get(switch, '')}')] = False"
            for switch in switches
        ]
    )
    add_switches = ""
    for switch in switches:
        add_switches += f'\n    if all or {switch}: self.switches.append("{switch}")'

    cmd_code = COMMAND_TMPL.format(
        routine=routine.name,
        switch_args=switch_args,
        add_switches=add_switches,
        all_help=_("Include all switched commands."),
    )

    command_strings = []
    for command in routine.commands:
        priority = f"{'[green]' if use_rich else ''}{command.priority}{'[/green]' if use_rich else ''}"
        cmd_str = f"{'[cyan]' if use_rich else ''}{command.command_str}{'[/cyan]' if use_rich else ''}"
        if command.options:
            if use_rich:
                opt_str = " ".join(
                    [
                        f"[blue]{k}[/blue]=[magenta]{v}[/magenta]"
                        for k, v in command.options.items()
                    ]
                )
            else:
                opt_str = " ".join([f"{k}={v}" for k, v in command.options.items()])
            cmd_str += f" ({opt_str})"
        switches_str = " | " if command.switches else ""
        switches_str += ", ".join(
            f"{'[yellow]' if use_rich else ''}{switch}{'[/yellow]' if use_rich else ''}"
            for switch in (command.switches or [])
        )
        command_strings.append(f"[{priority}] {cmd_str}{switches_str}")

    exec(cmd_code)

    if not use_rich:
        width = max([len(cmd) for cmd in command_strings])
    ruler = f"[underline]{' ' * width}[/underline]\n" if use_rich else "-" * width
    cmd_strings = "\n".join(command_strings)
    cmd_strings = f"{'[bright]' if use_rich else ''}{cmd_strings}{'[/bright]' if use_rich else ''}"
    lb = "\b\n"
    help_txt = (
        f"{lb}{routine.help_text}\n{ruler}{lb}{'' if use_rich else lb}{cmd_strings}\n"
    )
    grp = Command.group(
        help=help_txt, short_help=routine.help_text, invoke_without_command=True
    )(locals()[routine.name])

    @grp.command(name="list", help=_("List the commands that will be run."))
    def list(self):
        self._list()

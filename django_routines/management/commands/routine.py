import importlib
import os
import subprocess
import sys
import typing as t
from contextlib import contextmanager
from importlib.util import find_spec

import click
import typer
from django.core.management import CommandError, call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.translation import gettext as _
from django_typer.management import TyperCommand, get_command, initialize
from django_typer.types import Verbosity

from django_routines import (
    ManagementCommand,
    Routine,
    SystemCommand,
    get_routine,
    routines,
    to_cli_option,
    to_symbol,
)

if sys.version_info < (3, 9):
    from typing_extensions import Annotated
else:
    from typing import Annotated

RCommand = t.Union[ManagementCommand, SystemCommand]

width = 80
use_rich = find_spec("rich") is not None
if use_rich:
    from rich.console import Console

    width = Console().width

COMMAND_TMPL = """
def {routine_func}(
    self,
    ctx: typer.Context,
    subprocess: Annotated[bool, typer.Option("{subprocess_opt}", help="{subprocess_help}", show_default=False)] = {subprocess},
    atomic: Annotated[bool, typer.Option("{atomic_opt}", help="{atomic_help}", show_default=False)] = {atomic},
    continue_on_error: Annotated[bool, typer.Option("{continue_opt}", help="{continue_help}", show_default=False)] = {continue_on_error},
    all: Annotated[bool, typer.Option("--all", help="{all_help}")] = False,
    {switch_args}
):
    self.routine = "{routine}"
    self.switches = []
    {add_switches}
    subprocess = subprocess if (
        ctx.get_parameter_source("subprocess")
        is not click.core.ParameterSource.DEFAULT
    ) else None
    atomic = atomic if (
        ctx.get_parameter_source("atomic")
        is not click.core.ParameterSource.DEFAULT
    ) else None
    continue_on_error = continue_on_error if (
        ctx.get_parameter_source("continue_on_error")
        is not click.core.ParameterSource.DEFAULT
    ) else None
    if not ctx.invoked_subcommand:
        return self._run_routine(
            subprocess=subprocess,
            atomic=atomic,
            continue_on_error=continue_on_error
        )
    return self.{routine_func}
"""


class Command(TyperCommand, rich_markup_mode="rich"):  # type: ignore
    """
    A TyperCommand_ that reads the DJANGO_ROUTINES setting from settings and
    builds out a set of subcommands for each routine that when invoked will run
    those routines in order. Each routine also has a subcommand called ``list``
    that prints which commands will be executed and in what order given the
    switches the user has selected.

    .. note::

        If --verbosity is supplied, the value will be passed via options to any
        command in the routine that accepts it.
    """

    help = _("Run batches of commands configured in settings.")

    verbosity: int = 1
    switches: t.Set[str] = set()

    suppressed_base_arguments = set()

    _routine: t.Optional[Routine] = None
    _verbosity_passed: bool = False

    manage_script: str = sys.argv[0]

    @property
    def routine(self) -> t.Optional[Routine]:
        return self._routine

    @routine.setter
    def routine(self, routine: t.Union[str, Routine]):
        self._routine = (
            routine if isinstance(routine, Routine) else get_routine(str(routine))
        )

    @property
    def plan(self) -> t.List[RCommand]:
        """
        The Commands that make up the execution plan for the currently
        active routine and switches.
        """
        assert self.routine
        return self.routine.plan(self.switches)

    @initialize()
    def init(
        self,
        ctx: typer.Context,
        manage_script: Annotated[
            str,
            typer.Option(
                help=_(
                    "The manage script to use if running management commands as subprocesses."
                )
            ),
        ] = manage_script,
        verbosity: Verbosity = verbosity,
    ):
        self.verbosity = verbosity
        self._pass_verbosity = (
            ctx.get_parameter_source("verbosity")
            is not click.core.ParameterSource.DEFAULT
        )
        self.manage_script = manage_script

    def _run_routine(
        self,
        subprocess: t.Optional[bool] = None,
        atomic: t.Optional[bool] = None,
        continue_on_error: t.Optional[bool] = None,
    ):
        """
        Execute the current routine plan. If verbosity is zero, do not print the
        commands as they are run. Also use the stdout/stderr streams and color
        configuration of the routine command for each of the commands in the execution
        plan.
        """
        assert self.routine

        @contextmanager
        def noop():
            yield

        subprocess = subprocess if subprocess is not None else self.routine.subprocess
        is_atomic = atomic if atomic is not None else self.routine.atomic
        continue_on_error = (
            continue_on_error
            if continue_on_error is not None
            else self.routine.continue_on_error
        )
        ctx = transaction.atomic if is_atomic else noop
        with ctx():  # type: ignore
            for command in self.plan:
                try:
                    if isinstance(command, SystemCommand) or subprocess:
                        self._subprocess(command)
                    else:
                        self._call_command(command)
                except Exception as e:
                    if not continue_on_error:
                        raise e

    def _call_command(self, command: ManagementCommand):
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
            if self.verbosity > 0:
                self.secho(command.command_str, fg="cyan")
            call_command(cmd, *command.command_args, **options)
            if command.command_name == "makemigrations":
                importlib.invalidate_caches()
        except KeyError:
            raise CommandError(f"Command not found: {command.command_name}")

    def _subprocess(self, command: RCommand):
        options = []
        if isinstance(command, ManagementCommand):
            if command.options:
                # Make a good faith effort to convert options to cli compatible format
                # this is not very reliable which is why commands should avoid use of
                # options and instead use CLI strings
                cmd = get_command(command.command_name, BaseCommand)
                actions = getattr(
                    cmd.create_parser(self.manage_script, command.command_name),
                    "_actions",
                    [],
                )
                for opt, value in command.options.items():
                    for action in actions:
                        opt_strs = getattr(action, "option_strings", [])
                        if opt == getattr(action, "dest", None) and opt_strs:
                            if isinstance(value, bool):
                                if value:
                                    options.append(opt_strs[-1])
                            else:
                                options.append(f"--{opt}={str(value)}")
                            break

                if len(options) != len(command.options):
                    raise CommandError(
                        _(
                            "Failed to convert {command} options to CLI format: {unconverted}"
                        ).format(
                            command=command.command_name, unconverted=command.options
                        )
                    )

            args = [
                *(
                    [sys.executable, self.manage_script]
                    if self.manage_script.endswith(".py")
                    else [self.manage_script]
                ),
                *(
                    [command.command]
                    if isinstance(command.command, str)
                    else command.command
                ),
                *options,
            ]
        else:
            args = [command.command_name, *command.command_args]

        if self.verbosity > 0:
            self.secho(" ".join(args), fg="cyan")

        # todo make this async
        result = subprocess.run(args, env=os.environ.copy(), capture_output=True)
        self.stdout.write(result.stdout.decode())
        self.stderr.write(result.stderr.decode())
        if result.returncode > 0:
            raise CommandError(
                _(
                    "Subprocess command failed: {command} with return code {code}"
                ).format(command=" ".join(args), code=result.returncode)
            )
        return result.returncode

    def _list(self) -> None:
        """
        List the commands that are part of the execution plan given the active
        routine and switches.
        """
        for command in self.plan:
            priority = str(command.priority)
            cmd_str = command.command_str
            switches_str = " | " if command.switches else ""
            opt_str = (
                ", ".join([f"{k}={v}" for k, v in command.options.items()])
                if isinstance(command, ManagementCommand)
                else ""
            )
            if self.force_color or not self.no_color:
                priority = click.style(priority, fg="green")
                cmd_str = click.style(cmd_str, fg="cyan", bold=True)
                opt_str = (
                    ", ".join(
                        [
                            f"{click.style(k, 'blue')}={click.style(v, 'magenta')}"
                            for k, v in command.options.items()
                        ]
                    )
                    if isinstance(command, ManagementCommand)
                    else ""
                )
                switches_str += ", ".join(
                    click.style(to_cli_option(switch).lstrip("-"), fg="yellow")
                    for switch in (command.switches or [])
                )
            else:
                switches_str += ", ".join(
                    [
                        to_cli_option(switch).lstrip("-")
                        for switch in (command.switches or [])
                    ]
                )

            opt_str = f" ({opt_str})" if opt_str else ""
            self.secho(f"[{priority}] {cmd_str}{opt_str}{switches_str}")


for routine in routines():
    switches = routine.switches
    switch_args = ", ".join(
        [
            f"{to_symbol(switch, check_keyword=True)}: Annotated[bool, typer.Option('{to_cli_option(switch)}', help='{routine.switch_helps.get(switch, '')}')] = False"
            for switch in switches
        ]
    )
    add_switches = ""
    for switch in switches:
        add_switches += f'\n    if all or {to_symbol(switch, check_keyword=True)}: self.switches.append("{switch}")'

    cmd_code = COMMAND_TMPL.format(
        routine_func=to_symbol(routine.name, check_keyword=True),
        routine=routine.name,
        switch_args=switch_args,
        add_switches=add_switches,
        subprocess_opt="--no-subprocess" if routine.subprocess else "--subprocess",
        subprocess_help=(
            _("Do not run commands as subprocesses.")
            if routine.subprocess
            else _("Run commands as subprocesses.")
        ),
        subprocess=routine.subprocess,
        atomic_opt="--non-atomic" if routine.atomic else "--atomic",
        atomic_help=(
            _("Do not run all commands in the same transaction.")
            if routine.atomic
            else _("Run all commands in the same transaction.")
        ),
        atomic=routine.atomic,
        continue_opt="--halt" if routine.continue_on_error else "--continue",
        continue_help=(
            _("Halt if any command fails.")
            if routine.continue_on_error
            else _("Continue through the routine if any commands fail.")
        ),
        continue_on_error=routine.continue_on_error,
        all_help=_("Include all switched commands."),
    )

    command_strings = []
    for command in routine.commands:
        priority = f"{'[green]' if use_rich else ''}{command.priority}{'[/green]' if use_rich else ''}"
        cmd_str = f"{'[cyan]' if use_rich else ''}{command.command_str}{'[/cyan]' if use_rich else ''}"
        if isinstance(command, ManagementCommand) and command.options:
            if use_rich:
                opt_str = ", ".join(
                    [
                        f"[blue]{k}[/blue]=[magenta]{v}[/magenta]"
                        for k, v in command.options.items()
                    ]
                )
            else:
                opt_str = ", ".join([f"{k}={v}" for k, v in command.options.items()])
            cmd_str += f" ({opt_str})"
        switches_str = " | " if command.switches else ""
        switches_str += ", ".join(
            f"{'[yellow]' if use_rich else ''}{to_cli_option(switch).lstrip('-')}{'[/yellow]' if use_rich else ''}"
            for switch in (command.switches or [])
        )
        command_strings.append(f"[{priority}] {cmd_str}{switches_str}")

    exec(cmd_code)

    if not use_rich and command_strings:
        width = max([len(cmd) for cmd in command_strings])
    ruler = f"[underline]{' ' * width}[/underline]\n" if use_rich else "-" * width
    cmd_strings = "\n".join(command_strings)
    cmd_strings = f"{'[bright]' if use_rich else ''}{cmd_strings}{'[/bright]' if use_rich else ''}"
    lb = "\b\n"
    help_txt = (
        f"{lb}{routine.help_text}\n{ruler}{lb}{'' if use_rich else lb}{cmd_strings}\n"
    )
    grp = Command.group(
        name=routine.name.replace("_", "-"),
        help=help_txt,
        short_help=routine.help_text,
        invoke_without_command=True,
    )(locals()[to_symbol(routine.name, check_keyword=True)])

    @grp.command(name="list", help=_("List the commands that will be run."))
    def list(self):
        self._list()

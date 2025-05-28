import typing as t
from django_routines import Routine, Command
from tests import track_file
import json
from functools import partial


def noop(_: Command):
    pass


def _hook_track(
    routine: Routine,
    command: Command,
    prev_or_next: t.Optional[Command],
    options: t.Dict[str, t.Any],
    key: str = "hooks",
    label: str = "track",
    ret: bool = False,
    modify: t.Callable[[Command], None] = noop,
):
    """
    Pre-hook for the 'track' command to modify the command before execution.
    """
    if not track_file.is_file():
        track_file.write_text(
            json.dumps(
                {
                    "invoked": [],
                    key: [],
                    "passed_options": [],
                },
                indent=4,
            )
        )
    track = json.loads(track_file.read_text())
    track.setdefault(key, [])
    track[key].append(
        (
            label,
            routine.name,
            command.command_str,
            prev_or_next.command_str if prev_or_next else None,
            options,
            getattr(command.result, "stdout", command.result),
            getattr(prev_or_next.result, "stdout", prev_or_next.result)
            if prev_or_next
            else None,
        )
    )
    track_file.write_text(json.dumps(track, indent=4))
    modify(command)
    return ret


pre_hook = partial(_hook_track, key="pre_hooks")
post_hook = partial(_hook_track, key="post_hooks")

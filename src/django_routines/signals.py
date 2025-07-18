"""
All :pypi:`django-routines` specific :doc:`django:topics/signals` are defined here.

All signals contain a ``routine`` field that holds the name of the routine in question.
"""

from django.dispatch import Signal

routine_started = Signal()
"""
Signal sent when a routine is started, but before any commands have been run.

**Signature:**
``(sender, routine, **kwargs)``

:param sender: An instance of the running routine command.
:type sender: :class:`RoutineCommand <django_routines.management.commands.routine.Command>`
:param routine: The name of the routine being started.
:type routine: str
:param kwargs: The CLI options passed to the routine.
:type kwargs: typing.Dict[str, typing.Any]
"""


routine_failed = Signal()
"""
Signal sent when a routine is completed successfully. This will be called before the
exception is raised out of the command stack.

**Signature:**
``(sender, routine, failed_command, exception, **kwargs) -> bool``

.. tip::

    If you raise an :exc:`~django_routines.exceptions.ExitEarly` exception from
    a connected receiver, the routine will not propagate the exception and exit early
    gracefully.

:param sender: An instance of the running routine command.
:type sender: :class:`RoutineCommand <django_routines.management.commands.routine.Command>`
:param routine: The name of the routine that failed.
:type routine: str
:param failed_command: The plan index of the command that failed. See :ref:`plan_index`.
:type failed_command: int
:param exception: The exception that caused the routine to fail.
:type exception: Exception
:param kwargs: The CLI options passed to the routine.
:type kwargs: typing.Dict[str, typing.Any]
:return: If any connected receiver to this signal returns a truthy value the routine
    will proceed.
:rtype: typing.Optional[bool]
"""


routine_finished = Signal()
"""
Signal sent when a routine is completed successfully.

**Signature:**
``(sender, routine, early_exit, last_command, **kwargs) -> bool``

:param sender: An instance of the running routine command.
:type sender: :class:`RoutineCommand <django_routines.management.commands.routine.Command>`
:param routine: The name of the routine that completed.
:type routine: str
:param early_exit: True if a post hook triggered an early exit.
:type early_exit: bool
:param last_command: The plan index of the last command that was run in the routine
    (if any!). See :ref:`plan_index`.
:type last_command: typing.Optional[int]
:param kwargs: The CLI options passed to the routine.
:type kwargs: typing.Dict[str, typing.Any]
"""

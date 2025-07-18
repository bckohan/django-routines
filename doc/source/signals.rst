.. include:: ./refs.rst

.. _signals:

=======
Signals
=======

.. automodule:: django_routines.signals
   :members:
   :show-inheritance:
   :inherited-members:

.. _plan_index:

Plan Indexes
~~~~~~~~~~~~

When signals include a plan index, it refers to the index of the command in the routine's plan. The
index will refer to either a :class:`~django_routines.ManagementCommand` instance or a
:class:`~django_routines.SystemCommand` instance, depending on the type of command in the plan.
You can access the command object from the
:attr:`~django_routines.management.commands.routine.Command.plan` and index like so:

.. code-block:: python

   import typing as t
   from django.core.signals import Signal
   from django_routines.management.commands.routine import Command as RoutineCommand

   def handle_routine_failed(
      sender: RoutineCommand,            # the routine command instance (holds the plan)
      routine: str,                      # the name of the routine
      failed_command: int,               # the index of the command that failed in the plan
      exception: t.Optional[Exception],  # the exception that caused the failure
      signal: Signal,                    # the signal instance
      **kwargs                           # CLI options passed to the routine
   ):
       sender.plan[failed_command].command_name  # access the command name

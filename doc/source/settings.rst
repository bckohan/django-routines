.. include:: ./refs.rst

.. _settings:

========
Settings
========

DJANGO_ROUTINES
===============

.. setting:: DJANGO_ROUTINES

The configuration for :pypi:`django-routines` is stored in the :setting:`DJANGO_ROUTINES` setting
attribute. It is a dictionary structure that defines the routines and their commands. The structure
is complex so we provide :mod:`dataclasses` and functions that facilitate type safe definition of
the configuration.

Structure
---------

.. py:data:: DJANGO_ROUTINES
   :type: dict

   Django routines configuration dictionary. The keys in this dictionary are the names of the
   routines. Each routine is a dictionary containing a routine specification:

   .. py:data:: "<routine name>"
      :type: dict

      The routine specification dictionary contains the following keys:

      .. autosetting:: django_routines.Routine.help_text
         :no-index:

      .. autosetting:: django_routines.Routine.switch_helps
         :no-index:

      .. autosetting:: django_routines.Routine.subprocess
         :no-index:

      .. autosetting:: django_routines.Routine.atomic
         :no-index:

      .. autosetting:: django_routines.Routine.continue_on_error
         :no-index:

      .. autosetting:: django_routines.Routine.initialize
         :no-index:

      .. autosetting:: django_routines.Routine.finalize
         :no-index:

      .. autosetting:: django_routines.Routine.pre_hook
         :no-index:

      .. autosetting:: django_routines.Routine.post_hook
         :no-index:

      .. autosetting:: django_routines.Routine.commands
         :no-index:

         The command dictionaries must contain either a ``management`` or ``system``
         key that maps to a command specification.

         .. autosetting:: django_routines.RoutineCommand.command
            :keyname: management | system
            :no-index:

         .. autosetting:: django_routines.ManagementCommand.options
            :no-index:

         .. autosetting:: django_routines.RoutineCommand.priority
            :no-index:

         .. autosetting:: django_routines.RoutineCommand.switches
            :no-index:

         .. autosetting:: django_routines.RoutineCommand.pre_hook
            :no-index:

         .. autosetting:: django_routines.RoutineCommand.post_hook
            :no-index:

Examples
--------

The dictionary can be specified using any combination of these different methods.

.. tabs::

    .. tab:: Dict

      .. literalinclude:: ../../examples/dict.py
         :caption: settings.py
         :linenos:
         :lines: 3-34

    .. tab:: Data Classes

      The data classes provide a type-safe, editor friendly way to define the configuration.

      .. literalinclude:: ../../examples/dataclasses.py
         :caption: settings.py
         :linenos:
         :lines: 2-37

    .. tab:: Functions

      The shortcut functions are especially useful when composing routines across multiple
      different settings files. They allow you to not worry about definition order. The priority
      parameter allows for deterministic routine order even if the order of the functions changes.

      .. literalinclude:: ../../examples/functions.py
         :caption: settings.py
         :linenos:
         :lines: 2-39

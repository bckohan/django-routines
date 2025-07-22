.. include:: ./refs.rst
.. role:: big

===============
Django Routines
===============

.. django-admin:: routine

Configure batches of Django management commands in your settings files and run them all at once.
For example, batch together your common database maintenance tasks, deployment routines or any
other set of commands you need to run together. This helps single source general site maintenance
into your settings files keeping your code base DRY_.

If you have ever written one management command that calls other management commands this package
may help you.

:big:`Example`

Let's define two named routines, "package" and "deploy". The package routine will be a collection
of commands that we typically run to generate package artifacts (like migrations and transpiled
javascript). The deploy routine will be a collection of commands we typically run when deploying
the site for the first time on a new server or when we deploy version updates on the server.

.. note::

    Routine commands are run in the order they are registered, or by priority_.

There are two types of commands, management commands and system commands. The management commands
will be called in the same process space as routine unless ``--subprocess`` is specified in which
case they will use the same management script as routine was invoked with or whatever value you
supply to ``--manage-script``. System commands are always invoked as subprocesses.

In our settings file we may define these routines like this:

.. literalinclude:: ../../examples/readme.py
    :caption: settings.py
    :linenos:
    :lines: 2-41

The routine command will read our settings file and generate two subcommands, one called deploy
and one called package:

.. typer:: django_routines.management.commands.routine.Command:typer_app:package
    :prog: django-admin routine package
    :theme: dark
    :convert-png: latex

Now we can run all of our package routines with one command:

.. code-block:: bash

    ?> django-admin routine package
    makemigrations
    ...
    renderstatic
    ...
    poetry build
    ...

The deploy command has several switches that we can enable to run additional commands.

.. typer:: django_routines.management.commands.routine.Command:typer_app:deploy
    :prog: django-admin routine deploy
    :theme: dark
    :convert-png: latex

For example to deploy our demo on a new server we would run:

.. code-block:: bash

    ?> django-admin routine deploy --initial --demo
    migrate
    ...
    collectstatic
    ...
    shellcompletion install
    ...
    loaddata ./fixtures/demo.json
    ...
    touch /path/to/wsgi.py

:big:`Settings`

The :class:`~django_routines.ManagementCommand` dataclass, :func:`~django_routines.routine` and
:func:`~django_routines.command` helper functions in the example above make it easier for us to
work with the native configuration format which is a dictionary structure defined in the
:setting:`DJANGO-ROUTINES` setting attribute. For example the above configuration is equivalent to:

.. literalinclude:: ../../examples/readme_dict.py
    :caption: settings.py
    :linenos:
    :lines: 2-37


.. _priority:

:big:`Priorities`

If you are composing settings from multiple apps or source files using a utility like
:pypi:`django-split-settings` you may not be able to define all routines at once. You can use
priorities to make sure commands defined in a de-coupled way run in the correct order.

.. code-block:: python

    command("deploy", "makemigrations", priority=1)
    command("deploy", "migrate", priority=2)

:big:`Options`

When specifying arguments you may add them to the command tuple OR specify them as named
options in the style that will be passed to :func:`~django.core.management.call_command`:

.. code-block:: python

    # these two are equivalent
    command("package", ("makemigrations", "--no-header"))
    command("package", "makemigrations", no_header=True)

.. note::

    Lazy translations work as help_text for routines and switches.


.. _execution_controls:

:big:`Execution Controls`

There are several switches that can be used to control the execution of routines. Pass
these parameters when you define the Routine.

- ``atomic``: Run the routine in a transaction.
- ``continue_on_error``: Continue running the routine even if a command fails.

The default routine behavior for these execution controls can be overridden on the command
line.

:big:`Pre/Post Hooks`

:attr:`~django_routines.PreHook` and :attr:`~django_routines.PostHook` functions can be attached to
routines and commands. These functions provide:

- a way to execute arbitrary code before or after the routine or command execution.
- full access to the routine or command context (options and results).
- the ability to halt execution of the routine early or skip individual commands.
- the ability to modify the routine or command context.

.. _rationale:

:big:`Rationale`

When does it make sense to configure routines in Django settings? Its generally convenient to group
common management pathways into easily discoverable and executable aggregations of subroutines.
This is usually done in supporting shell scripts or just files and in most cases that is
appropriate. If your goal is to keep your Django deployment as tight and self contained as possible
and the deployment is not generally very complex, using :pypi:`django-routines` can make a lot of
sense. It can eliminate extra dependencies on a shell scripting environment or just files and can
keep this logic packaged with your installable wheel.

Django routines also encourages stronger command logic encapsulation. It allows complex workflows
to be broken down into smaller, more manageable commands that can be attached and invoked together
as part of larger routines.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   settings
   signals
   reference
   changelog

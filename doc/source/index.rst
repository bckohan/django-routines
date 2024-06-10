.. include:: ./refs.rst
.. role:: big

===============
Django Routines
===============

Configure batches of Django management commands in your settings files and run them all at once.
For example, batch together your common database maintenance tasks, deployment routines or any
other set of commands you need to run together. This helps single source general site maintenance
into your settings files keeping your code base DRY_.

:big:`Example`

Let's define two named routines, "package" and "deploy". The package routine will be a collection
of commands that we typically run to generate package artifacts (like migrations and transpiled
javascript). The deploy routine will be a collection of commands we typically run when deploying
the site for the first time on a new server or when we deploy version updates on the server.

.. note::

    Routine commands are run in the order they are registered, or by priority_.

There are two types of commands, management commands and system commands. The management commands
will be called in the same process space as routine unless --subprocess is specified in which case
they will use the same management script as routine was invoked with or whatever value you supply
to --manage-script. System commands are always invoked as subprocesses.

In our settings file we may define these routines like this:

.. literalinclude:: ../../examples/readme.py
    :caption: settings.py
    :linenos:
    :lines: 2-33

The routine command will read our settings file and generate two subcommands, one called deploy
and one called package:

.. typer:: django_routines.management.commands.routine.Command:typer_app:package
    :prog: ./manage.py routine package
    :theme: dark
    :convert-png: latex

Now we can run all of our package routines with one command:

.. code-block:: console

    ?> ./manage.py routine package
    makemigrations
    ...
    renderstatic
    ...

The deploy command has several switches that we can enable to run additional commands.

.. typer:: django_routines.management.commands.routine.Command:typer_app:deploy
    :prog: ./manage.py routine deploy
    :theme: dark
    :convert-png: latex

For example to deploy our demo on a new server we would run:

.. code-block:: console

    ?> ./manage.py routine deploy --initial --demo
    migrate
    ...
    collectstatic
    ...
    shellcompletion install
    ...
    loaddata ./fixtures/demo.json
    ...


:big:`Settings`

The :class:`~django_routines.ManagementCommand` dataclass, :func:`django_routines.routine` and
:func:`django_routines.command` helper functions in the example above make it easier for us to
work with the native configuration format which is a dictionary structure defined in the
``DJANGO_ROUTINES`` setting attribute. For example the above configuration is equivalent to:

.. literalinclude:: ../../examples/readme_dict.py
    :caption: settings.py
    :linenos:
    :lines: 2-33


.. _priority:

:big:`Priorities`

If you are composing settings from multiple apps or source files using a utility like
django-split-settings_ you may not be able to define all routines at once. You can use
priorities to make sure commands defined in a de-coupled way run in the correct order.

.. code-block:: python

    command("deploy", "makemigrations", priority=1)
    command("deploy", "migrate", priority=2)

:big:`Options`

When specifying arguments you may add them to the command tuple OR specify them as named
options in the style that will be passed to call_command_:

.. code-block:: python

    # these two are equivalent
    command("package", ("makemigrations", "--no-header"))
    command("package", "makemigrations", no_header=True)

.. note::

    Lazy translations work as help_text for routines and switches.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   reference
   changelog

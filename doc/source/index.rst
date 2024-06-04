.. include:: ./refs.rst
.. role:: big

===============
Django Routines
===============

Build up batches of Django management commands in your settings files and run them all at once.
For example, batch together your common database maintenance tasks, deployment routines or any
other set of commands you need to run together. This helps single source general site maintenance
into your settings files keeping your code base DRY_.

:big:`Installation`

1. Clone django-routines from GitHub_ or install a release off PyPI_ :

    .. code:: bash

        pip install django-routines

    rich_ is a powerful library for rich text and beautiful formatting in the terminal.
    It is not required, but highly recommended for the best experience:

    .. code:: bash

        pip install "django-routines[rich]"


2. Add ``django_routines`` to your ``INSTALLED_APPS`` setting:

    .. code:: python

        INSTALLED_APPS = [
            ...
            'django_routines',
        ]

3. Optionally add ``django_typer`` to your ``INSTALLED_APPS`` setting:

    .. code:: python

        INSTALLED_APPS = [
            ...
            'django_typer',
        ]

   *You only need to install django_typer as an app if you want to use the shellcompletion command
   to enable tab-completion or if you would like django-typer to install*
   `rich traceback rendering <https://django-typer.readthedocs.io/en/latest/howto.html#configure-rich-stack-traces>`_
   *for you - which it does by default if rich is also installed.*


:big:`Basic Example`

.. todo:: Add a basic example


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   reference
   changelog

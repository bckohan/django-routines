.. include:: ./refs.rst

============
Installation
============

1. Install :pypi:`django-routines` from pypi or clone from GitHub_:

    .. code:: bash

        pip install django-routines

    :pypi:`rich` is a powerful library for rich text and beautiful formatting in the terminal.
    It is not required, but highly recommended for the best experience:

    .. code:: bash

        pip install "django-routines[rich]"


2. Add ``django_routines`` to your :setting:`INSTALLED_APPS` setting:

    .. code:: python

        INSTALLED_APPS = [
            ...
            'django_routines',
            'django_typer',  # optional!
        ]

   *You only need to install* :pypi:`django-typer` *as an app if you want to use the*
   :django-admin:`shellcompletion` *command to*
   :doc:`enable tab-completion <django-typer:shell_completion>` *or if you would like*
   :pypi:`django-typer` *to install*
   :ref:`rich traceback rendering <django-typer:configure-rich-exception-tracebacks>`
   *for you - which it does by default if rich is also installed.*

3. Create routines by adding them to the :setting:`DJANGO_ROUTINES` directive in your settings file.

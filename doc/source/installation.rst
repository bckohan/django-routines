.. include:: ./refs.rst

============
Installation
============

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
            'django_typer',  # optional!
        ]

   *You only need to install* django-typer_ *as an app if you want to use the shellcompletion
   command to* :doc:`enable tab-completion <django-typer:shell_completion>` *or if you would like*
   django-typer_ *to install*
   :ref:`rich traceback rendering <django-typer:configure-rich-exception-tracebacks>`
   *for you - which it does by default if rich is also installed.*

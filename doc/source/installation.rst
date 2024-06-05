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

   *You only need to install django_typer as an app if you want to use the shellcompletion command
   to* `enable tab-completion <https://django-typer.readthedocs.io/en/latest/shell_completion.html>`_
   *or if you would like django-typer to install*
   `rich traceback rendering <https://django-typer.readthedocs.io/en/latest/howto.html#configure-rich-stack-traces>`_
   *for you - which it does by default if rich is also installed.*

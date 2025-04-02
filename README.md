# django-routines


[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI version](https://badge.fury.io/py/django-routines.svg)](https://pypi.python.org/pypi/django-routines/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/django-routines.svg)](https://pypi.python.org/pypi/django-routines/)
[![PyPI djversions](https://img.shields.io/pypi/djversions/django-routines.svg)](https://pypi.org/project/django-routines/)
[![PyPI status](https://img.shields.io/pypi/status/django-routines.svg)](https://pypi.python.org/pypi/django-routines)
[![Documentation Status](https://readthedocs.org/projects/django-routines/badge/?version=latest)](https://django-routines.readthedocs.io/en/latest/)
[![Code Cov](https://codecov.io/gh/bckohan/django-routines/branch/main/graph/badge.svg?token=0IZOKN2DYL)](https://codecov.io/gh/bckohan/django-routines)
[![Test Status](https://github.com/bckohan/django-routines/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/bckohan/django-routines/actions/workflows/test.yml?query=branch:main)
[![Lint Status](https://github.com/bckohan/django-routines/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/bckohan/django-routines/actions/workflows/lint.yml?query=branch:main)
[![Published on Django Packages](https://img.shields.io/badge/Published%20on-Django%20Packages-0c3c26)](https://djangopackages.org/packages/p/django-routines/)


Configure batches of Django management commands in your settings files and run them all at once. For example, batch together your common database maintenance tasks, deployment routines or any other set of commands you need to run together. This helps single source general site maintenance into your settings files keeping your code base [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself).

## Example

Let's define two named routines, "package" and "deploy". The package routine will be a collection of commands that we typically run to generate package artifacts (like migrations and transpiled javascript). The deploy routine will be a collection of commands we typically run when deploying the site for the first time on a new server or when we deploy version updates on the server.

**Routine commands are run in the order they are registered, or by [priority](#priorities).**

There are two types of commands, management commands and system commands. The management commands will be called in the same process space as routine unless --subprocess is specified in which case they will use the same management script as routine was invoked with or whatever value you supply to --manage-script. System commands are always invoked as subprocesses.

In our settings file we may define these routines like this:

```python
from django_routines import (
    ManagementCommand,
    SystemCommand,
    command,
    system,
    routine
)

# register routines and their help text
routine(
    name="package",
    help_text=(
        "Generate pre-package artifacts like migrations and transpiled "
        "javascript."
    )
)
# you may register commands on a routine after defining a routine (or before!)
command("package", "makemigrations")
command("package", "renderstatic")
system("package", "poetry", "build")

routine(
    "deploy",
    "Deploy the site application into production.",

    # you may also specify commands inline using the ManagementCommand dataclass
    ManagementCommand(
        ("routine", "package"), switches=["prepare"]
    ),  # routine commands can be other routines!
    ManagementCommand("migrate"),
    ManagementCommand("collectstatic"),
    ManagementCommand(("shellcompletion", "install"), switches=["initial"]),
    ManagementCommand(("loaddata", "./fixtures/demo.json"), switches=["demo"]),
    SystemCommand(("touch", "/path/to/wsgi.py")),

    # define switches that toggle commands on and off
    prepare="Generate artifacts like migrations and transpiled javascript.",
    initial="Things to do on the very first deployment on a new server.",
    demo="Load the demo data.",
)
```

The routine command will read our settings file and generate two subcommands, one called deploy and one called package:

![package](https://raw.githubusercontent.com/bckohan/django-routines/main/examples/package.svg)

Now we can run all of our package routines with one command:

```bash
    ?> ./manage.py routine package
    makemigrations
    ...
    renderstatic
    ...
    poetry build
    ...
```

The deploy command has several switches that we can enable to run additional commands.

![deploy](https://raw.githubusercontent.com/bckohan/django-routines/main/examples/deploy.svg)

For example to deploy our demo on a new server we would run:

```bash
    ?> ./manage.py routine deploy --initial --demo
    migrate
    ...
    collectstatic
    ...
    shellcompletion install
    ...
    loaddata ./fixtures/demo.json
    ...
    touch /path/to/wsgi.py
```

## Settings

The [ManagementCommand](https://django-routines.readthedocs.io/en/latest/reference.html#django_routines.ManagementCommand) dataclass, [routine](https://django-routines.readthedocs.io/en/latest/reference.html#django_routines.routine) and [command](https://django-routines.readthedocs.io/en/latest/reference.html#django_routines.command) helper functions in the example above make it easier for us to work with the native configuration format which is a dictionary structure defined in the ``DJANGO_ROUTINES`` setting attribute. For example the above configuration is equivalent to:

```python
DJANGO_ROUTINES = {
    "deploy": {
        "commands": [
            {"command": ("routine", "package"), "switches": ["prepare"]},
            {"command": "migrate"},
            {"command": "collectstatic"},
            {
                "command": ("shellcompletion", "install"),
                "switches": ["initial"],
            },
            {
                "command": ("loaddata", "./fixtures/demo.json"),
                "switches": ["demo"],
            },
            {"command": ("touch", "/path/to/wsgi.py"), "kind": "system"},
        ],
        "help_text": "Deploy the site application into production.",
        "name": "deploy",
        "switch_helps": {
            "demo": "Load the demo data.",
            "initial": "Things to do on the very first deployment on a new "
                       "server.",
            "prepare": "Generate artifacts like migrations and transpiled "
                       "javascript.",
        },
    },
    "package": {
        "commands": [
            {"command": "makemigrations"},
            {"command": "renderstatic"},
            {"command": ("poetry", "build"), "kind": "system"},
        ],
        "help_text": "Generate pre-package artifacts like migrations and "
                     "transpiled javascript.",
        "name": "package",
    },
}
```


## Priorities

If you are composing settings from multiple apps or source files using a utility like [django-split-settings](https://pypi.org/project/django-split-settings/) you may not be able to define all routines at once. You can use priorities to make sure commands defined in a de-coupled way run in the correct order.

```python
    command("deploy", "makemigrations", priority=1)
    command("deploy", "migrate", priority=2)
```

## Options

When specifying arguments you may add them to the command tuple OR specify them as named options in the style that will be passed to [call_command](https://docs.djangoproject.com/en/stable/ref/django-admin/#django.core.management.call_command):

```python
    # these two are equivalent
    command("package", "makemigrations", "--no-header")
    command("package", "makemigrations", no_header=True)
```

## Execution Controls

There are several switches that can be used to control the execution of routines. Pass these parameters when you define the Routine.

- ``atomic``: Run the routine in a transaction.
- ``continue_on_error``: Continue running the routine even if a command fails.

The default routine behavior for these execution controls can be overridden on the command line.


## Installation


1. Clone django-routines from [GitHub](https://github.com/bckohan/django-routines) or install a release off [PyPI](https://pypi.python.org/pypi/django-routines) :

    ```bash
        pip install django-routines
    ```

    [rich](https://rich.readthedocs.io/) is a powerful library for rich text and beautiful formatting in the terminal. It is not required, but highly recommended for the best experience:

    ```bash
        pip install "django-routines[rich]"
    ```


2. Add ``django_routines`` to your ``INSTALLED_APPS`` setting:

    ```python
        INSTALLED_APPS = [
            ...
            'django_routines',
            'django_typer',  # optional!
        ]
    ```

   *You only need to install [django_typer](https://github.com/bckohan/django-typer) as an app if you want to use the shellcompletion command to [enable tab-completion](https://django-typer.readthedocs.io/en/latest/shell_completion.html) or if you would like django-typer to install [rich traceback rendering](https://django-typer.readthedocs.io/en/latest/howto.html#configure-rich-stack-traces) for you - which it does by default if rich is also installed.*

## Rationale

When does it make sense to configure routines in Django settings? Its generally convenient to group common management pathways into easily discoverable and executable aggregations of subroutines. This is usually done in supporting shell scripts or just files and in most cases that is appropriate. If your goal is to keep your Django deployment as tight and self contained as possible and the deployment is not generally very complex, using django-routines can make a lot of sense. It can eliminate extra dependencies on a shell scripting environment or just files and can keep this logic packaged with your installable wheel.

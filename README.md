# django-routines


[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![PyPI version](https://badge.fury.io/py/django-routines.svg)](https://pypi.python.org/pypi/django-routines/)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/django-routines.svg)](https://pypi.python.org/pypi/django-routines/)
[![PyPI djversions](https://img.shields.io/pypi/djversions/django-routines.svg)](https://pypi.org/project/django-routines/)
[![PyPI status](https://img.shields.io/pypi/status/django-routines.svg)](https://pypi.python.org/pypi/django-routines)
[![Documentation Status](https://readthedocs.org/projects/django-routines/badge/?version=latest)](http://django-routines.readthedocs.io/?badge=latest/)
[![Code Cov](https://codecov.io/gh/bckohan/django-routines/branch/main/graph/badge.svg?token=0IZOKN2DYL)](https://codecov.io/gh/bckohan/django-routines)
[![Test Status](https://github.com/bckohan/django-routines/workflows/test/badge.svg)](https://github.com/bckohan/django-routines/actions/workflows/test.yml)
[![Lint Status](https://github.com/bckohan/django-routines/workflows/lint/badge.svg)](https://github.com/bckohan/django-routines/actions/workflows/lint.yml)


Configure batches of Django management commands in your settings files and run them all at once.
For example, batch together your common database maintenance tasks, deployment routines or any
other set of commands you need to run together. This helps single source general site maintenance
into your settings files keeping your code base [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself).

## Example

Let's define two named routines, "package" and "deploy". The package routine will be a collection
of commands that we typically run to generate package artifacts (like migrations and transpiled
javascript). The deploy routine will be a collection of commands we typically run when deploying
the site for the first time on a new server or when we deploy version updates on the server.

**Routine commands are run in the order they are registered, or by [priority](#priorities).**

In our settings file we may define these routines like this:

```python
from django_routines import RoutineCommand, command, routine

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

routine(
    "deploy",
    "Deploy the site application into production.",

    # you may also specify commands inline using the RoutineCommand dataclass
    RoutineCommand(
        ("routine", "package"), switches=["prepare"]
    ),  # routine commands can be other routines!
    RoutineCommand("migrate"),
    RoutineCommand("collectstatic"),
    RoutineCommand(("shellcompletion", "install"), switches=["initial"]),
    RoutineCommand(("loaddata", "./fixtures/demo.json"), switches=["demo"]),

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
```

## Settings

The [RoutineCommand](https://django-routines.readthedocs.io/en/latest/reference.html#django_routines.RoutineCommand) dataclass, [routine](https://django-routines.readthedocs.io/en/latest/reference.html#django_routines.routine) and [command](https://django-routines.readthedocs.io/en/latest/reference.html#django_routines.command) helper functions in the example above make it easier for us to work with the native configuration format which is a dictionary structure defined in the ``DJANGO_ROUTINES`` setting attribute. For example the above configuration is equivalent to:

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

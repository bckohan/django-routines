from . import *  # noqa: F403

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

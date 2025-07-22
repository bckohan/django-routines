from . import *  # noqa: F403

DJANGO_ROUTINES = {
    "deploy": {
        "commands": [
            {"management": ("routine", "package"), "switches": ["prepare"]},
            {"management": "migrate"},
            {"management": "collectstatic"},
            {
                "management": ("shellcompletion", "install"),
                "switches": ["initial"],
            },
            {
                "management": ("loaddata", "./fixtures/demo.json"),
                "switches": ["demo"],
            },
            {"system": ("touch", "/path/to/wsgi.py")},
        ],
        "help_text": "Deploy the site application into production.",
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
            {"management": "makemigrations"},
            {"management": "renderstatic"},
            {"system": ("uv", "build")},
        ],
        "help_text": "Generate pre-package artifacts like migrations and "
                     "transpiled javascript.",
    },
}

from . import *  # noqa: F403

DJANGO_ROUTINES = {
    "<routine_name>": {
        "commands": [
            {
                "management": ("<management_command>", "<arg1>"),
                "options": {},  # kwargs for call_command
                "priority": 0,  # an integery priority for execution order
                "switches": ["<switch_name>"],  # optional switch enablers
                "pre_hook": None,  # or a callable pre hook function
                "post_hook": None,  # or a callable post hook function
            },
            {
                "system": ("<cmd>", "<arg1>"),
                "priority": 0,  # an integery priority for execution order
                "switches": ["<switch_name>"],  # optional switch enablers
                "pre_hook": None,  # or a callable pre hook function
                "post_hook": None,  # or a callable post hook function
            },
        ],
        "help_text": "<help_text>",
        "switch_helps": {
            "<switch_name>": "<switch_help_text>.",
        },
        "subprocess": False,  # or True
        "atomic": False,  # or True
        "continue_on_error": False,  # or True
        "initialize": None,  # or a callable initialize function
        "finalize": None,  # or a callable finalize function
        "pre_hook": None,  # or a callable pre hook function
        "post_hook": None,  # or a callable post hook function
    },
}

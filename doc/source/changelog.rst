==========
Change Log
==========

v1.6.0 (2025-07-22)
===================

* Implemented `Allow callback to be specified as import strings. <https://github.com/bckohan/django-routines/issues/54>`_
* Implemented `Add an initialize callback. <https://github.com/bckohan/django-routines/issues/53>`_
* Implemented `Add a finalize callback option for routines. <https://github.com/bckohan/django-routines/issues/52>`_
* Implemented `Should not require the name to be listed on the routine when specified as a dictionary. <https://github.com/bckohan/django-routines/issues/51>`_
* Implemented `Deprecate "kind" in favor of "management" vs "system" <https://github.com/bckohan/django-routines/issues/50>`_

  The ``kind`` key is deprecated and should now be used as the ``command`` key in place of
  ``command``. For example:

    .. code-block:: python

        "commands": [
            {"command": ("migrate"), "kind": "management"},
            {"command": ("touch", "/var/www/site/wsgi.py"), "kind": "system"},

            # the above will still work but should be rewritten as:

            {"management": ("migrate"),}
            {"system": ("touch", "/var/www/site/wsgi.py")},
        ]

* Fixed `--subprocess,--atomic, and --continue options not working <https://github.com/bckohan/django-routines/issues/49>`_
* Implemented `Add signals for routine started/ended. <https://github.com/bckohan/django-routines/issues/45>`_
* Fixed `KeyError catch can hide errors and produce misleading statements <https://github.com/bckohan/django-routines/issues/44>`_

v1.5.1 (2025-07-17)
===================

* Docs `Use django-admin role for command references. <https://github.com/bckohan/django-routines/issues/48>`_

v1.5.0 (2025-05-28)
===================

* Implemented `Support python 3.14 <https://github.com/bckohan/django-routines/issues/39>`_
* Implemented `Support function pre and post hooks to be run prior to and after given commands. <https://github.com/bckohan/django-routines/issues/9>`_

v1.4.0 (2024-04-02)
===================

* Implemented `Use intersphinx for cross doc references <https://github.com/bckohan/django-routines/issues/33>`_
* Implemented `Switch from poetry -> uv <https://github.com/bckohan/django-routines/issues/32>`_
* Implemented `Support Django 5.2 <https://github.com/bckohan/django-routines/issues/31>`_

v1.3.0 (2024-02-18)
===================

* Implemented `Remove support for python 3.8 <https://github.com/bckohan/django-routines/issues/30>`_
* Implemented `Upgrade to django-typer 3.x <https://github.com/bckohan/django-routines/issues/29>`_
* Implemented `stdout/stderr streaming from subprocesses <https://github.com/bckohan/django-routines/issues/15>`_

v1.2.1 (2024-08-26)
===================

* Fixed `Switch rtd theme to furo. <https://github.com/bckohan/django-routines/issues/27>`_
* Fixed `Support python 3.13 <https://github.com/bckohan/django-routines/issues/26>`_

v1.2.0 (2024-07-27)
===================

* `Option to run routine within a transaction. <https://github.com/bckohan/django-routines/issues/24>`_
* `Option to fail fast or proceed on failures. <https://github.com/bckohan/django-routines/issues/10>`_


v1.1.3 (2024-07-17)
===================

* `Allow routine names that conflict with python keywords (i.e. import) <https://github.com/bckohan/django-routines/issues/21>`_

v1.1.2 (2024-07-15)
===================

* `Support Django 5.1 <https://github.com/bckohan/django-routines/issues/19>`_

v1.1.1 (2024-07-15)
===================

* `Allow hyphens (-) in switches. <https://github.com/bckohan/django-routines/issues/17>`_

v1.1.0 (2024-07-10)
===================

* `Invalidate importlib caches if command is makemigrations. <https://github.com/bckohan/django-routines/issues/13>`_
* `Rationale for why settings is a good place to put routines. <https://github.com/bckohan/django-routines/issues/8>`_
* `Command type for system commands (i.e. non-management commands) to be run as subprocesses <https://github.com/bckohan/django-routines/issues/7>`_
* `Option to run management commands as subprocesses instead of in the same process space. <https://github.com/bckohan/django-routines/issues/6>`_

v1.0.2 (2024-06-05)
===================

* `Update import deprecation for django-typer 2.1+ <https://github.com/bckohan/django-routines/issues/4>`_

v1.0.1 (2024-06-05)
===================

* `Help example images dont have the correct usage line. <https://github.com/bckohan/django-routines/issues/3>`_


v1.0.0 (2024-06-05)
===================

* Initial production/stable release.

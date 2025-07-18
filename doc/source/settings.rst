.. include:: ./refs.rst

.. _settings:

========
Settings
========

DJANGO_ROUTINES
---------------

.. setting:: DJANGO_ROUTINES

The configuration for :pypi:`django-routines` is stored in the :setting:`DJANGO_ROUTINES` setting
attribute. It is a dictionary structure that defines the routines and their commands. The structure
is complex so we provide :mod:`dataclasses` and functions that facilitate type
safe definition of the configuration.

Example:

.. tabs::

    .. tab:: Dict

        .. literalinclude:: ../../examples/readme_dict.py
            :caption: settings.py
            :linenos:
            :lines: 2-39

    .. tab:: Data Classes
        .. literalinclude:: ../../examples/readme.py
            :caption: settings.py
            :linenos:
            :lines: 2-39
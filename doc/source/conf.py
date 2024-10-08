import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

import django

import django_routines

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "examples.readme")
django.setup()

sys.path.append(str(Path(__file__).parent.parent / "tests"))

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = "django_routines"
copyright = f"2024-{datetime.now().year}, Brian Kohan"
author = "Brian Kohan"

# The full version, including alpha/beta/rc tags
release = django_routines.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinxcontrib.typer"
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "furo"
html_theme_options = {
    "source_repository": "https://github.com/bckohan/django-routines/",
    "source_branch": "main",
    "source_directory": "doc/source",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = [
    '_static',
]
html_css_files = [
    "style.css",
]

todo_include_todos = True

latex_engine = "xelatex"

suppress_warnings = ["app.add_directive"]


def setup(app):
    # https://sphinxcontrib-typer.readthedocs.io/en/latest/howto.html#build-to-multiple-formats
    if Path(app.doctreedir).exists():
        shutil.rmtree(app.doctreedir)
    return app

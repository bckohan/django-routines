import os
import shutil
import sys
from pathlib import Path
from sphinx.ext.autodoc import AttributeDocumenter
import django

sys.path.append(str(Path(__file__).parent / 'ext'))
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent / "tests"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "examples.readme")
django.setup()
import django_routines

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
project = django_routines.__title__
copyright = django_routines.__copyright__
author = django_routines.__author__
release = django_routines.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinxcontrib_django',
    'sphinx.ext.intersphinx',
    "sphinx_autosetting",
    "sphinx.ext.autodoc",
    "sphinx.ext.todo",
    "sphinxcontrib.typer",
    'sphinx_tabs.tabs',
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

intersphinx_mapping = {
    "django": (
        "https://docs.djangoproject.com/en/stable",
        "https://docs.djangoproject.com/en/stable/_objects/",
    ),
    "django-typer": ("https://django-typer.readthedocs.io/en/stable", None),
    "rich": ("https://rich.readthedocs.io/en/stable", None),
    "python": ('https://docs.python.org/3', None)
}

autodoc_default_options = {
    'show-inheritance': True,
    # Add other autodoc options here if desired, e.g.:
    # 'members': True,
    # 'inherited-members': True,
}
# In your Sphinx conf.py
autodoc_typehints = "description"
autodoc_typehints_format = "short"
autodoc_class_signature = "separated"
autodoc_member_order = 'bysource'


def pypi_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    from docutils import nodes
    url = f"https://pypi.org/project/{text}/"
    node = nodes.reference(rawtext, text, refuri=url, **options)
    return [node], []


def setup(app):
    from docutils.parsers.rst import roles
    # https://sphinxcontrib-typer.readthedocs.io/en/latest/howto.html#build-to-multiple-formats
    if Path(app.doctreedir).exists():
        shutil.rmtree(app.doctreedir)
    app.add_crossref_type(directivename="django-admin", rolename="django-admin")
    roles.register_local_role('pypi', pypi_role)
    return app

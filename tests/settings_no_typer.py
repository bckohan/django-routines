from .settings import *

INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django_typer"]

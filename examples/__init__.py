import os
from pathlib import Path

# Set default terminal width for help outputs - necessary for
# testing help output in CI environments.
os.environ["TERMINAL_WIDTH"] = "80"

BASE_DIR = Path(__file__).resolve().parent.parent


INSTALLED_APPS = [
    "tests.django_routines_tests",
    "django_routines",
    "django_typer",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STATIC_URL = "static/"

SECRET_KEY = "fake"

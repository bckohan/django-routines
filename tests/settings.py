import os
from pathlib import Path
from django_routines import (
    routine,
    command,
    RoutineCommand,
    get_routine,
)
from django.utils.translation import gettext_lazy as _

# Set default terminal width for help outputs - necessary for
# testing help output in CI environments.
os.environ["TERMINAL_WIDTH"] = "80"

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-$druy$m$nio-bkagw_%=@(1w)q0=k^mk_5sfk3zi9#4v!%mh*u"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "tests.django_routines_tests",
    "django_routines",
    "django_typer",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "TEST": {"NAME": BASE_DIR / "db.sqlite3"},
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = "en-us"
# LANGUAGE_CODE = 'de'


TIME_ZONE = "UTC"

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = "/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


SETTINGS_FILE = 1

ROOT_URLCONF = "tests.urls"


routine(
    "deploy",
    _("Deploy the site application into production."),
    RoutineCommand(("migrate",), priority=1),
    RoutineCommand(("collectstatic",), priority=5),
    prepare=_("Prepare the deployment."),
    demo="Deploy the demo.",
)

command("deploy", "makemigrations", priority=0, switches=["prepare"])
command("deploy", "renderstatic", priority=4)
command(
    "deploy", "loaddata", "./fixtures/initial_data.json", priority=6, switches=["demo"]
)

assert get_routine("deploy").name == "deploy"


routine(
    "test",
    _("Test Routine 1"),
    RoutineCommand(
        ("track", "0"), priority=1, switches=("initial",), options={"verbosity": 0}
    ),
    RoutineCommand(("track", "1"), priority=4),
)

command("test", "track", "2", priority=0, switches=("initial", "demo"))
command("test", "track", "3", priority=3, demo=2)
command("test", "track", "4", priority=3, demo=6)
command("test", "track", "5", priority=6, switches=["demo"])

routine(
    "bad",
    _("Bad command test routine"),
    RoutineCommand(("track", "0")),
    RoutineCommand(("does_not_exist",)),
    RoutineCommand(("track", "1")),
)

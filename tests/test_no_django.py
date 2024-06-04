from django.test import override_settings, TestCase
from .test_core import CoreTests


@override_settings(
    INSTALLED_APPS=[
        "tests.django_routines_tests",
        "django_routines",
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
    ]
)
class NoDjangoTyperInstalledTests(CoreTests, TestCase):
    pass

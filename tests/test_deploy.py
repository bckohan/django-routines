"""
Miscellaneous tests - mostly for coverage
"""

from io import StringIO
from django.core.management import call_command
from django.test import TestCase


class TestDeploy(TestCase):
    def test_deploy_routine(self):
        out = StringIO()
        err = StringIO()
        call_command("routine", "deploy", "--prepare", stdout=out, stderr=err)
        self.assertTrue(out.getvalue())
        self.assertFalse(err.getvalue().strip())

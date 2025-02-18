"""
Miscellaneous tests - mostly for coverage
"""

from django_routines import ManagementCommand, SystemCommand


def test_to_dict_return():
    assert isinstance(
        ManagementCommand.from_dict(ManagementCommand("test")), ManagementCommand
    )
    assert isinstance(SystemCommand.from_dict(SystemCommand("test")), SystemCommand)

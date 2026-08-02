# coding: utf-8

# Copyright (C) 2026 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""
The exceptions are injected by SCSIDeviceCommandExceptionMeta at runtime and
declared as ClassVar[Type[Exception]] for mypy, in two separate places. This
pins them together.

An injected name with no declaration still works at runtime, but mypy rejects
the use and types it as Any -- so the failure is silent in both directions
unless something compares the sets. A declaration with no injection is worse:
AttributeError on first use.
"""

import ast
import inspect
import unittest

from pyscsi.pyiscsi.iscsi_device import ISCSIDevice
from pyscsi.pyscsi.scsi_command import SCSICommand
from pyscsi.pyscsi.scsi_device import SCSIDevice

# Both families, since all three classes use the combined metaclass.
EXPECTED = {
    "ACAActive",
    "BusyStatus",
    "CheckCondition",
    "CommandNotImplemented",
    "ConditionsMet",
    "MissingBlocksizeException",
    "OpcodeException",
    "ReservationConflict",
    "TaskAborted",
    "TaskSetFull",
}

HOSTS = (SCSICommand, SCSIDevice, ISCSIDevice)


def _declared(cls):
    """Names annotated as ClassVar[Type[Exception]] in the class body."""
    tree = ast.parse(inspect.getsource(inspect.getmodule(cls)))
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == cls.__name__:
            return {
                stmt.target.id
                for stmt in node.body
                if isinstance(stmt, ast.AnnAssign)
                and isinstance(stmt.target, ast.Name)
                and "Exception]" in ast.unparse(stmt.annotation)
            }
    raise AssertionError("no class body found for %s" % cls.__name__)


def _injected(cls):
    return {
        name
        for name in dir(cls)
        if isinstance(getattr(cls, name, None), type)
        and issubclass(getattr(cls, name), BaseException)
    }


class ExceptionInjection(unittest.TestCase):
    def test_declared_matches_injected(self):
        for cls in HOSTS:
            with self.subTest(cls=cls.__name__):
                self.assertEqual(_declared(cls), _injected(cls))

    def test_every_host_carries_both_families(self):
        for cls in HOSTS:
            with self.subTest(cls=cls.__name__):
                self.assertEqual(_injected(cls), EXPECTED)

    def test_exceptions_are_distinct_per_host(self):
        # Documented behaviour: SCSIDevice.CheckCondition is not
        # ISCSIDevice.CheckCondition, so catching one will not catch the other.
        self.assertIsNot(SCSIDevice.CheckCondition, ISCSIDevice.CheckCondition)
        self.assertIsNot(SCSIDevice.OpcodeException, SCSICommand.OpcodeException)

    def test_each_is_usable_as_an_exception(self):
        # CheckCondition derives from SCSICheckCondition, which parses a sense
        # buffer rather than taking a message. The other nine are plain
        # Exception subclasses.
        sense = bytearray(18)
        sense[0] = 0x70  # current error, fixed format
        sense[2] = 0x05  # ILLEGAL REQUEST
        sense[7] = 10  # additional sense length
        sense[12] = 0x20  # INVALID COMMAND OPERATION CODE

        for cls in HOSTS:
            for name in sorted(EXPECTED):
                with self.subTest(cls=cls.__name__, exception=name):
                    exc = getattr(cls, name)
                    arg = sense if name == "CheckCondition" else "raised in test"
                    with self.assertRaises(exc):
                        raise exc(arg)


if __name__ == "__main__":
    unittest.main()

# SPDX-FileCopyrightText: 2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import importlib
import pkgutil
import sys
import unittest

import pyscsi


def _walk_module_names():
    """Every module under the pyscsi package, including subpackages."""
    return sorted(
        info.name
        for info in pkgutil.walk_packages(pyscsi.__path__, prefix="pyscsi.")
        if not info.ispkg
    )


class ImportEveryModuleTest(unittest.TestCase):
    """Tripwire for import-time metaprogramming.

    Several command modules mutate shared state while being imported: they
    attach enum tables onto SCSICommand, and pyscsi/pyscsi/__init__.py drives
    submodule imports off a hand-maintained __all__ of module-name strings.
    None of that is exercised by the CDB tests, so a refactor can break a
    module that no other test imports. Importing all of them catches it.
    """

    def test_every_module_imports(self):
        failures = []
        for name in _walk_module_names():
            try:
                importlib.import_module(name)
            except Exception as exc:  # noqa: BLE001 - report, don't mask
                failures.append(f"{name}: {exc!r}")
        self.assertEqual([], failures)

    def test_command_modules_are_covered(self):
        # Guard against the walk silently finding nothing, which would make
        # test_every_module_imports pass vacuously.
        names = _walk_module_names()
        cdb_modules = [n for n in names if ".scsi_cdb_" in n]
        self.assertGreater(len(cdb_modules), 30, names)

    def test_scsi_device_is_imported_transitively(self):
        # `from .pyscsi import *` in pyscsi/__init__.py pulls in scsi_device
        # via the __all__ module-name list. mypy cannot model that, so the
        # mechanism will have to change; this pins the behaviour it must keep.
        importlib.import_module("pyscsi")
        self.assertIn("pyscsi.pyscsi.scsi_device", sys.modules)

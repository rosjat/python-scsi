# coding: utf-8

# Copyright (C) 2026 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""
Every field layout table in the package, checked against the notation contract.

CheckDict is Sequence[Any] because the two notations cannot be written as a
Union mypy can check, so nothing static rejects a malformed entry. This walks
every *_bits table and every BitsTable member in the package and runs
validate_check_dict over it, which covers far more entries than the two
functions that read them.
"""

import importlib
import inspect
import pkgutil
import unittest
from types import ModuleType
from typing import Any, Dict, Iterator, List, Tuple

import pyscsi
from pyscsi.utils.converter import validate_check_dict
from pyscsi.utils.exception import NotSupportedArgumentError
from pyscsi.utils.table import BitsTable


def _modules() -> Iterator[ModuleType]:
    for info in pkgutil.walk_packages(pyscsi.__path__, prefix="pyscsi."):
        yield importlib.import_module(info.name)


def _tables() -> Iterator[Tuple[str, Dict[str, Any]]]:
    """Yield (label, check_dict) for every layout table reachable in pyscsi."""
    seen = set()

    def looks_like_a_table(value: Any) -> bool:
        # Matched on shape, not name: the layouts are spelled _cdb_bits,
        # _segment_descriptor_bits_stream_to_block and
        # _device_specific_cscd_descriptor_parameters_block alike. Value tables
        # are excluded by their int values, code tables by their int keys.
        return (
            isinstance(value, dict)
            and bool(value)
            and all(isinstance(k, str) for k in value)
            and all(isinstance(v, (list, tuple)) for v in value.values())
        )

    def emit(label: str, value: Any) -> Iterator[Tuple[str, Dict[str, Any]]]:
        # Dedupe on the table itself: star-imports make the same object reachable
        # under many names.
        if isinstance(value, BitsTable):
            for member_name in value.keys:
                member = getattr(value, member_name)
                if looks_like_a_table(member) and id(member) not in seen:
                    seen.add(id(member))
                    yield "%s.%s" % (label, member_name), member
        elif looks_like_a_table(value) and id(value) not in seen:
            seen.add(id(value))
            yield label, value

    for module in _modules():
        for name, obj in vars(module).items():
            yield from emit("%s.%s" % (module.__name__, name), obj)

            if inspect.isclass(obj) and obj.__module__ == module.__name__:
                for attr, value in vars(obj).items():
                    yield from emit(
                        "%s.%s.%s" % (module.__name__, obj.__name__, attr), value
                    )


class CheckDictShapes(unittest.TestCase):
    def test_every_table_in_the_package_is_well_formed(self) -> None:
        count = 0
        entries = 0
        for label, table in _tables():
            with self.subTest(table=label):
                validate_check_dict(table, label)
            count += 1
            entries += len(table)

        # Guards against the walk silently finding nothing; it reaches 143
        # tables and 764 entries today.
        self.assertGreater(count, 100, "found only %d tables" % count)
        self.assertGreater(entries, 600, "found only %d entries" % entries)

    def test_malformed_entries_are_rejected(self) -> None:
        # Deliberately malformed, so the entries have no common type.
        cases: List[Tuple[str, Any]] = [
            ("not a sequence", {"f": 42}),
            ("wrong length", {"f": [0xFF, 0, 1, 2]}),
            ("bitmask not an int", {"f": ["x", 0]}),
            ("zero bitmask", {"f": [0, 0]}),
            ("negative offset", {"f": [0xFF, -1]}),
            ("unknown blob type", {"f": ("q", 0, 4)}),
            ("zero blob length", {"f": ("b", 0, 0)}),
            ("blob offset not an int", {"f": ("b", "x", 4)}),
        ]
        for name, table in cases:
            with self.subTest(case=name):
                with self.assertRaises(NotSupportedArgumentError):
                    validate_check_dict(table)

    def test_both_valid_notations_are_accepted(self) -> None:
        validate_check_dict(
            {
                "legacy": [0xFF, 0],
                "wide": [0xFFFFFFFFFFFFFFFF, 2],
                "blob": ("b", 8, 8),
                "word": ("w", 10, 10),
                "dword": ("dw", 4, 2),
            }
        )


if __name__ == "__main__":
    unittest.main()

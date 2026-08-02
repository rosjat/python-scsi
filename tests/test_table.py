# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg <ronniesahlberg@gmail.com>
# Copyright (C) 2015 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_enum_command import smc
from pyscsi.utils.exception import NotSupportedArgumentError
from pyscsi.utils.table import BitsTable, Table, ValueTable

table_dict = {
    "A": 1,
    "B": 2,
    "C": 3,
}


class TableConstructionTest(unittest.TestCase):
    def test_fails_on_passing_multiple_args(self) -> None:
        # Table takes a single positional mapping. The wrong types are the
        # point of these two tests, so mypy is told to allow them here.
        with self.assertRaises(TypeError):
            ValueTable(1, 2, 3)  # type: ignore[call-arg, arg-type]

    def test_fails_on_passing_a_non_mapping(self) -> None:
        with self.assertRaises(NotSupportedArgumentError):
            ValueTable((1, 2, 3))  # type: ignore[arg-type]

    def test_fails_on_no_arguments(self) -> None:
        with self.assertRaises(NotSupportedArgumentError):
            ValueTable()

    def test_fails_on_mapping_and_keywords_together(self) -> None:
        with self.assertRaises(NotSupportedArgumentError):
            ValueTable(table_dict, D=4)

    def test_empty_mapping_is_allowed(self) -> None:
        # OpCode passes {} for commands without service actions.
        self.assertEqual([], ValueTable({}).keys)


class TableAccessTest(unittest.TestCase):
    def test_from_mapping(self) -> None:
        i = ValueTable(table_dict)
        self.assertEqual(i.A, 1)
        self.assertEqual(i.B, 2)
        self.assertEqual(i.C, 3)
        self.assertEqual(i[1], "A")
        self.assertEqual(i[2], "B")
        self.assertEqual(i[3], "C")
        self.assertEqual(i[4], "")

    def test_from_keywords(self) -> None:
        a = ValueTable(A=1, B=2, C=3)
        self.assertEqual(a.A, 1)
        self.assertEqual(a.B, 2)
        self.assertEqual(a.C, 3)
        self.assertEqual(a[1], "A")
        self.assertEqual(a[4], "")

    def test_unknown_member_raises_attribute_error(self) -> None:
        i = ValueTable(table_dict)
        with self.assertRaises(AttributeError):
            i.NOPE

    def test_private_name_raises_rather_than_recursing(self) -> None:
        # __getattr__ must not recurse when _members is not yet bound.
        i = ValueTable(table_dict)
        with self.assertRaises(AttributeError):
            i._not_a_slot

    def test_keys_is_a_property_in_insertion_order(self) -> None:
        self.assertEqual(["A", "B", "C"], ValueTable(table_dict).keys)

    def test_container_protocol(self) -> None:
        i = ValueTable(table_dict)
        self.assertEqual(3, len(i))
        self.assertIn("A", i)
        self.assertNotIn("Z", i)
        self.assertEqual(["A", "B", "C"], list(i))
        self.assertEqual([("A", 1), ("B", 2), ("C", 3)], list(i.items()))

    def test_duplicate_values_are_kept(self) -> None:
        # The reason these are not stdlib enums: stdlib would alias D onto A.
        i = ValueTable({"A": 1, "D": 1})
        self.assertEqual(1, i.A)
        self.assertEqual(1, i.D)
        self.assertEqual(["A", "D"], i.keys)
        self.assertEqual("A", i[1])


class TableSubclassTest(unittest.TestCase):
    def test_subclasses_are_real_classes(self) -> None:
        self.assertIsInstance(ValueTable(table_dict), Table)
        self.assertIsInstance(BitsTable({"page": {"x": [0xFF, 0]}}), Table)

    def test_bits_table_holds_field_notation(self) -> None:
        bits = BitsTable({"page": {"x": [0xFF, 0]}})
        self.assertEqual({"x": [0xFF, 0]}, bits.page)


class OpcodeTableTest(unittest.TestCase):
    def test_opcode_members(self) -> None:
        self.assertEqual(smc.WRITE_BUFFER.value, 0x3B)
        self.assertEqual(smc.WRITE_BUFFER.name, "WRITE_BUFFER")

    def test_repr_shows_name_and_hex_value(self) -> None:
        self.assertEqual("WRITE_BUFFER - 3b", repr(smc.WRITE_BUFFER))

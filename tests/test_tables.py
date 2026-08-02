# SPDX-FileCopyrightText: 2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

import pyscsi.pyscsi.scsi_enum_command as enum_command
import pyscsi.pyscsi.scsi_enum_inquiry as enum_inquiry
import pyscsi.pyscsi.scsi_enum_readdiscinformation as enum_rdi
from pyscsi.pyscsi.scsi_opcode import OpCode

OPCODE_TABLES = {
    "spc": (enum_command.spc, 27),
    "sbc": (enum_command.sbc, 78),
    "ssc": (enum_command.ssc, 51),
    "smc": (enum_command.smc, 46),
    "mmc": (enum_command.mmc, 48),
}


class OpcodeTableTest(unittest.TestCase):
    """Structural guard for the opcode tables.

    The tables are accessed by attribute everywhere, so a member lost or
    renamed while reworking them would only surface as an AttributeError in
    whichever command happens to be exercised. These assertions pin the shape.
    """

    def test_member_counts(self) -> None:
        for name, (table, expected) in OPCODE_TABLES.items():
            with self.subTest(table=name):
                self.assertEqual(expected, len(table.keys))

    def test_keys_are_unique(self) -> None:
        for name, (table, _) in OPCODE_TABLES.items():
            with self.subTest(table=name):
                keys = table.keys
                self.assertEqual(len(keys), len(set(keys)))

    def test_members_are_opcodes(self) -> None:
        for name, (table, _) in OPCODE_TABLES.items():
            with self.subTest(table=name):
                for key in table.keys:
                    opcode = getattr(table, key)
                    self.assertIsInstance(opcode, OpCode)
                    self.assertIsInstance(opcode.value, int)

    def test_opcode_name_matches_key_except_known_deviations(self) -> None:
        """A table key and its OpCode.name normally agree. One does not.

        SMC_OPCODE_1B is deliberate: it is the synthetic name for an opcode
        carrying service actions, inverted relative to SPC_OPCODE_A3 and
        SBC_OPCODE_9E where the synthetic name is the key rather than the
        OpCode.name. Its key is already the correct T10 name for 0x1B on
        media changers.

        Two sbc entries used to disagree with the T10 operation code list
        (https://www.t10.org/lists/op-num.htm) and have since been corrected;
        this assertion is what keeps any new divergence visible.
        """
        mismatches = {
            (name, key, getattr(table, key).name)
            for name, (table, _) in OPCODE_TABLES.items()
            for key in table.keys
            if key != getattr(table, key).name
        }
        self.assertEqual(
            {("smc", "OPEN_CLOSE_IMPORT_EXPORT_ELEMENT", "SMC_OPCODE_1B")},
            mismatches,
        )

    def test_corrected_names_match_the_standard(self) -> None:
        # T10 op-num: BBh is REDUNDANCY GROUP (OUT), BFh is VOLUME SET (OUT),
        # BEh is VOLUME SET (IN). smc spells all three per the standard; sbc
        # previously did not.
        for table in (enum_command.sbc, enum_command.smc):
            with self.subTest(table=table):
                self.assertEqual(
                    "REDUNDANCY_GROUP_OUT", table.REDUNDANCY_GROUP_OUT.name
                )
                self.assertEqual(0xBB, table.REDUNDANCY_GROUP_OUT.value)
                self.assertEqual("VOLUME_SET_OUT", table.VOLUME_SET_OUT.name)
                self.assertEqual(0xBF, table.VOLUME_SET_OUT.value)
                self.assertEqual("VOLUME_SET_IN", table.VOLUME_SET_IN.name)
                self.assertEqual(0xBE, table.VOLUME_SET_IN.value)

    def test_known_opcodes(self) -> None:
        self.assertEqual(0x12, enum_command.spc.INQUIRY.value)
        self.assertEqual(0x88, enum_command.sbc.READ_16.value)
        self.assertEqual(0x42, enum_command.sbc.UNMAP.value)
        self.assertEqual(0x51, enum_command.mmc.READ_DISC_INFORMATION.value)
        self.assertEqual(0xA5, enum_command.smc.MOVE_MEDIUM.value)

    def test_reverse_lookup(self) -> None:
        table = enum_command.spc
        self.assertEqual("INQUIRY", table[table.INQUIRY])

    def test_reverse_lookup_miss_returns_empty_string(self) -> None:
        # Deliberate contract: a miss yields "", not a KeyError. tools/ relies
        # on this when printing unknown values.
        self.assertEqual("", enum_command.spc[object()])
        self.assertEqual("", enum_inquiry.DEVICE_TYPE[0xDEADBEEF])

    def test_multiplexed_opcodes_are_reachable(self) -> None:
        # Opcodes sharing a byte across service actions live under synthetic
        # names and are fetched by their last two characters.
        self.assertEqual(0xA3, enum_command.spc.SPC_OPCODE_A3.value)
        self.assertEqual(0x9E, enum_command.sbc.SBC_OPCODE_9E.value)


class DuplicateValueTest(unittest.TestCase):
    """Duplicate values must survive.

    This is the reason the tables are not stdlib enum.Enum: stdlib silently
    aliases members that share a value, keeping only the first name. The 0xA3
    service-action table has 30 names across just 17 distinct values, so
    aliasing would erase 13 of them.
    """

    def test_service_actions_keep_aliased_names(self) -> None:
        actions = enum_command.spc.SPC_OPCODE_A3.serviceaction
        keys = actions.keys
        values = [getattr(actions, key) for key in keys]

        self.assertEqual(30, len(keys))
        self.assertEqual(17, len(set(values)))

        # Every colliding name must still resolve independently.
        self.assertEqual(0x05, actions.REPORT_DEVICE_IDENTIFIER)
        self.assertEqual(0x05, actions.REPORT_IDENTIFYING_INFORMATION)
        self.assertEqual(0x0B, actions.REPORT_ALIASES)
        self.assertEqual(0x0B, actions.CHANGE_ALIASES)
        self.assertEqual(0x0B, actions.WRITE_32)

    def test_reverse_lookup_picks_first_insertion_order_match(self) -> None:
        actions = enum_command.spc.SPC_OPCODE_A3.serviceaction
        name = actions[0x05]
        self.assertIn(
            name, ("REPORT_DEVICE_IDENTIFIER", "REPORT_IDENTIFYING_INFORMATION")
        )
        self.assertEqual(0x05, getattr(actions, name))


class ValueTableTest(unittest.TestCase):
    def test_scsi_status_members(self) -> None:
        self.assertEqual(9, len(enum_command.SCSI_STATUS.keys))
        self.assertEqual(0x00, enum_command.SCSI_STATUS.GOOD)

    def test_disc_type_key_set(self) -> None:
        self.assertEqual(
            {"CD-DA or CD-ROM", "CD-I", "CD-ROM XA", "UNDEFINED"},
            set(enum_rdi.DISC_TYPE.keys),
        )

    def test_disc_information_data_type_key_set(self) -> None:
        self.assertEqual(
            {
                "STANDARD_DISC_INFORMATION",
                "TRACK_RESOURCES_INFORMATION",
                "POW_RESOURCES_DISC_INFORMATION",
            },
            set(enum_rdi.DISC_INFORMATION_DATA_TYPE.keys),
        )

    def test_inquiry_tables_roundtrip(self) -> None:
        for name in ("DEVICE_TYPE", "CODE_SET", "ASSOCIATION", "DESIGNATOR", "VPD"):
            table = getattr(enum_inquiry, name)
            with self.subTest(table=name):
                self.assertGreater(len(table.keys), 0)
                for key in table.keys:
                    value = getattr(table, key)
                    # Reverse lookup must land on a name with the same value;
                    # it need not be `key` itself when values are duplicated.
                    self.assertEqual(value, getattr(table, table[value]))

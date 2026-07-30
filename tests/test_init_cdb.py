# SPDX-FileCopyrightText: 2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_command import SCSICommand
from pyscsi.pyscsi.scsi_enum_command import sbc
from pyscsi.pyscsi.scsi_opcode import OpCode


class InitCdbTest(unittest.TestCase):
    """CDB length is derived from the operation code's group code.

    See the group table in SCSICommand.init_cdb. Group 3 (0x60-0x7F) and the
    vendor-specific groups 6 and 7 have no fixed length and must be rejected.
    """

    def _cdb_len(self, value):
        return len(SCSICommand.init_cdb(OpCode("TEST", value, {})))

    def test_fixed_length_groups(self):
        cases = [
            # group 0 -> 6
            (0x00, 6),
            (0x12, 6),
            (0x1F, 6),
            # groups 1 and 2 -> 10
            (0x20, 10),
            (0x28, 10),
            (0x5F, 10),
            # group 4 -> 16
            (0x80, 16),
            (0x88, 16),
            (0x9F, 16),
            # group 5 -> 12
            (0xA0, 12),
            (0xA8, 12),
            (0xBF, 12),
        ]
        for value, expected in cases:
            with self.subTest(opcode=hex(value)):
                self.assertEqual(expected, self._cdb_len(value))

    def test_group_3_is_rejected(self):
        # 0x7E is the extended CDB and 0x7F the variable length CDB; neither
        # has a length that init_cdb can derive from the opcode alone.
        for value in (0x60, 0x7E, 0x7F):
            with self.subTest(opcode=hex(value)):
                with self.assertRaises(SCSICommand.OpcodeException) as ctx:
                    self._cdb_len(value)
                self.assertIn("variable length", str(ctx.exception))

    def test_vendor_specific_is_rejected(self):
        for value in (0xC0, 0xE0, 0xFF):
            with self.subTest(opcode=hex(value)):
                with self.assertRaises(SCSICommand.OpcodeException) as ctx:
                    self._cdb_len(value)
                self.assertIn("vendor specific", str(ctx.exception))

    def test_declared_7f_opcode_is_rejected_with_a_reason(self):
        # The opcode tables are a full registry of the standard, so 0x7F is
        # declared whether or not a command is built on it. Reaching init_cdb
        # with a real table entry must fail with an explanation rather than a
        # bare exception.
        with self.assertRaises(SCSICommand.OpcodeException) as ctx:
            SCSICommand.init_cdb(sbc.SBC_OPCODE_7F)
        self.assertIn("0x7F", str(ctx.exception))
        self.assertIn("variable length", str(ctx.exception))

    def test_every_declared_opcode_either_sizes_or_explains(self):
        # No opcode in any table may fail with an empty message.
        from pyscsi.pyscsi import scsi_enum_command as enum_command

        for name in ("spc", "sbc", "ssc", "smc", "mmc"):
            table = getattr(enum_command, name)
            for key in table.keys:
                opcode = getattr(table, key)
                with self.subTest(table=name, opcode=key):
                    try:
                        self.assertIn(
                            len(SCSICommand.init_cdb(opcode)), (6, 10, 12, 16)
                        )
                    except SCSICommand.OpcodeException as exc:
                        self.assertNotEqual("", str(exc))

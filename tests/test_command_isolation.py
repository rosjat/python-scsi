# coding: utf-8

# Copyright (C) 2026 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_cdb_inquiry import Inquiry
from pyscsi.pyscsi.scsi_cdb_read16 import Read16
from pyscsi.pyscsi.scsi_command import SCSICommand
from pyscsi.pyscsi.scsi_enum_command import sbc
from tests.mock_device import MockDevice, MockSCSI


class CommandIsolationTest(unittest.TestCase):
    """
    Constructing one command must not change how another decodes its own CDB.

    _cdb_bits and _cdb used to be assigned to SCSICommand rather than to the
    instance, so the most recently constructed command decided the field map
    for every command object alive.
    """

    def test_unmarshall_uses_its_own_field_map(self):
        with MockSCSI(MockDevice(sbc)) as s:
            inquiry = s.inquiry(alloclen=128)
            raw = bytearray(inquiry.cdb)
            before = inquiry.unmarshall_cdb(raw)

            # A second, longer command with a completely different layout.
            s.readcapacity16()

            after = inquiry.unmarshall_cdb(raw)

        self.assertEqual(
            before,
            after,
            "constructing another command changed how an existing one decodes",
        )
        self.assertEqual(before["alloc_len"], 128)

    def test_class_level_marshall_uses_its_own_field_map(self):
        with MockSCSI(MockDevice(sbc)) as s:
            s.inquiry(alloclen=128)
            # Constructed last, so it owned the shared class state.
            s.readcapacity16()

        cdb = {"opcode": sbc.INQUIRY.value, "evpd": 0, "page_code": 0, "alloc_len": 128}
        self.assertEqual(Inquiry.unmarshall_cdb(Inquiry.marshall_cdb(cdb)), cdb)

    def test_cdb_length_follows_the_command(self):
        with MockSCSI(MockDevice(sbc)) as s:
            inquiry = s.inquiry(alloclen=128)
            readcap = s.readcapacity16()

            # INQUIRY is group 0 (6 bytes), READ CAPACITY(16) group 4 (16).
            self.assertEqual(len(inquiry.cdb), 6)
            self.assertEqual(len(readcap.cdb), 16)

    def test_base_class_state_is_not_mutated(self):
        with MockSCSI(MockDevice(sbc)) as s:
            s.inquiry(alloclen=128)

        self.assertEqual(
            SCSICommand._cdb_bits,
            {},
            "constructing a command overwrote the base class field map",
        )


if __name__ == "__main__":
    unittest.main()

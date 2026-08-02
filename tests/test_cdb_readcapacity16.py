# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg <ronniesahlberg@gmail.com>
# Copyright (C) 2015 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_cdb_readcapacity16 import ReadCapacity16
from pyscsi.pyscsi.scsi_enum_command import sbc
from pyscsi.utils.converter import scsi_ba_to_int
from tests.mock_device import MockDevice, MockSCSI


class CdbReadcapacity16Test(unittest.TestCase):
    def test_main(self) -> None:
        with MockSCSI(MockDevice(sbc)) as s:
            r = s.readcapacity16(alloclen=37)
            raw_cdb = r.cdb
            self.assertEqual(raw_cdb[0], s.device.opcodes.SBC_OPCODE_9E.value)
            self.assertEqual(
                raw_cdb[1],
                s.device.opcodes.SBC_OPCODE_9E.serviceaction.READ_CAPACITY_16,
            )
            self.assertEqual(raw_cdb[2:10], bytearray(8))
            self.assertEqual(scsi_ba_to_int(raw_cdb[10:14]), 37)
            self.assertEqual(raw_cdb[14:16], bytearray(2))
            cdb = r.unmarshall_cdb(raw_cdb)
            self.assertEqual(cdb["opcode"], s.device.opcodes.SBC_OPCODE_9E.value)
            self.assertEqual(
                cdb["service_action"],
                s.device.opcodes.SBC_OPCODE_9E.serviceaction.READ_CAPACITY_16,
            )
            self.assertEqual(cdb["alloc_len"], 37)

            d = ReadCapacity16.unmarshall_cdb(ReadCapacity16.marshall_cdb(cdb))
            self.assertEqual(d, cdb)

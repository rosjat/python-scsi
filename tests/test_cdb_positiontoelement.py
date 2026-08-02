# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg <ronniesahlberg@gmail.com>
# Copyright (C) 2015 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_cdb_positiontoelement import PositionToElement
from pyscsi.pyscsi.scsi_enum_command import smc
from pyscsi.utils.converter import scsi_ba_to_int
from tests.mock_device import MockDevice, MockSCSI


class CdbPositiontoelementTest(unittest.TestCase):
    def test_main(self) -> None:
        with MockSCSI(MockDevice(smc)) as s:
            m = s.positiontoelement(15, 32, invert=1)
            raw_cdb = m.cdb
            self.assertEqual(raw_cdb[0], s.device.opcodes.POSITION_TO_ELEMENT.value)
            self.assertEqual(raw_cdb[1], 0)
            self.assertEqual(scsi_ba_to_int(raw_cdb[2:4]), 15)
            self.assertEqual(scsi_ba_to_int(raw_cdb[4:6]), 32)
            self.assertEqual(raw_cdb[8], 0x01)
            cdb = m.unmarshall_cdb(raw_cdb)
            self.assertEqual(cdb["opcode"], s.device.opcodes.POSITION_TO_ELEMENT.value)
            self.assertEqual(cdb["medium_transport_address"], 15)
            self.assertEqual(cdb["destination_address"], 32)
            self.assertEqual(cdb["invert"], 1)

            d = PositionToElement.unmarshall_cdb(PositionToElement.marshall_cdb(cdb))
            self.assertEqual(d, cdb)

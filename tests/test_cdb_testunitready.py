# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg <ronniesahlberg@gmail.com>
# Copyright (C) 2015 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_cdb_testunitready import TestUnitReady
from pyscsi.pyscsi.scsi_enum_command import sbc
from tests.mock_device import MockDevice, MockSCSI


class CdbTestunitreadyTest(unittest.TestCase):
    def test_main(self) -> None:
        with MockSCSI(MockDevice(sbc)) as s:
            w = s.testunitready()
            raw_cdb = w.cdb
            self.assertEqual(raw_cdb[0], s.device.opcodes.TEST_UNIT_READY.value)
            self.assertEqual(raw_cdb[1], 0)
            self.assertEqual(raw_cdb[2], 0)
            self.assertEqual(raw_cdb[3], 0)
            self.assertEqual(raw_cdb[4], 0)
            self.assertEqual(raw_cdb[5], 0)
            cdb = w.unmarshall_cdb(raw_cdb)
            self.assertEqual(cdb["opcode"], s.device.opcodes.TEST_UNIT_READY.value)

            d = TestUnitReady.unmarshall_cdb(TestUnitReady.marshall_cdb(cdb))
            self.assertEqual(d, cdb)

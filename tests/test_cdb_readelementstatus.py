#!/usr/bin/env python
# coding: utf-8
# Copyright (C) 2014 by Ronnie Sahlberg <ronniesahlberg@gmail.com>
# Copyright (C) 2015 by Markus Rosjat <markus.rosjat@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2.1 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import unittest

from pyscsi.utils.converter import scsi_ba_to_int
from pyscsi.pyscsi.scsi_enum_command import smc
from pyscsi.pyscsi import scsi_enum_readelementstatus as READELEMENTSTATUS
from pyscsi.pyscsi.scsi_cdb_readelementstatus import ReadElementStatus
from mock_device import MockDevice, MockSCSI

class CdbReadelementstatusTest(unittest.TestCase):
    def test_main(self):

        with MockSCSI(MockDevice(smc)) as s:
            # cdb for SMC: ReadElementStatus
            r = s.readelementstatus(300, 700, element_type=READELEMENTSTATUS.ELEMENT_TYPE.STORAGE, voltag=1, curdata=1, dvcid=1)
            cdb = r.cdb
            self.assertEqual(cdb[0], s.device.opcodes.READ_ELEMENT_STATUS.value)
            self.assertEqual(cdb[1], 0x10 | READELEMENTSTATUS.ELEMENT_TYPE.STORAGE)
            self.assertEqual(scsi_ba_to_int(cdb[2:4]), 300)
            self.assertEqual(scsi_ba_to_int(cdb[4:6]), 700)
            self.assertEqual(cdb[6], 0x03)
            self.assertEqual(scsi_ba_to_int(cdb[7:10]), 16384)
            cdb = r.unmarshall_cdb(cdb)
            self.assertEqual(cdb['opcode'], s.device.opcodes.READ_ELEMENT_STATUS.value)
            self.assertEqual(cdb['voltag'], 1)
            self.assertEqual(cdb['element_type'], READELEMENTSTATUS.ELEMENT_TYPE.STORAGE)
            self.assertEqual(cdb['starting_element_address'], 300)
            self.assertEqual(cdb['num_elements'], 700)
            self.assertEqual(cdb['curdata'], 1)
            self.assertEqual(cdb['dvcid'], 1)
            self.assertEqual(cdb['alloc_len'], 16384)

            d = ReadElementStatus.unmarshall_cdb(ReadElementStatus.marshall_cdb(cdb))
            self.assertEqual(d, cdb)

if __name__ == '__main__':
    unittest.main()

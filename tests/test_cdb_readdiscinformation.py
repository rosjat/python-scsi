# SPDX-FileCopyrightText: 2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_cdb_readdiscinformation import ReadDiscInformation
from pyscsi.pyscsi.scsi_command import SCSICommand
from pyscsi.pyscsi.scsi_enum_command import mmc
from pyscsi.utils.converter import scsi_ba_to_int
from tests.mock_device import MockDevice, MockSCSI


class CdbReadDiscInformationTest(unittest.TestCase):
    """ReadDiscInformation had no test at all.

    It is one of the modules that bulk-attaches enum tables onto SCSICommand
    at import time, so it breaks easily when those tables are reworked.
    """

    def test_main(self) -> None:
        with MockSCSI(MockDevice(mmc)) as s:
            r = s.readdiscinformation(data_type=0, alloc_len=1024)
            raw_cdb = r.cdb
            self.assertEqual(raw_cdb[0], s.device.opcodes.READ_DISC_INFORMATION.value)
            self.assertEqual(raw_cdb[1], 0)
            self.assertEqual(scsi_ba_to_int(raw_cdb[7:9]), 1024)

            cdb = r.unmarshall_cdb(raw_cdb)
            self.assertEqual(
                cdb["opcode"], s.device.opcodes.READ_DISC_INFORMATION.value
            )
            self.assertEqual(cdb["data_type"], 0)
            self.assertEqual(cdb["alloc_len"], 1024)

            d = ReadDiscInformation.unmarshall_cdb(
                ReadDiscInformation.marshall_cdb(cdb)
            )
            self.assertEqual(d, cdb)

    def test_data_type_encoded(self) -> None:
        with MockSCSI(MockDevice(mmc)) as s:
            r = s.readdiscinformation(data_type=1, alloc_len=64)
            self.assertEqual(r.cdb[1], 1)
            self.assertEqual(scsi_ba_to_int(r.cdb[7:9]), 64)

    def test_enum_tables_attached(self) -> None:
        # These land on the class via the setattr loop in the module body.
        # However that attachment is expressed, the values must not change.
        dt = ReadDiscInformation.DISC_INFORMATION_DATA_TYPE
        self.assertEqual(dt.STANDARD_DISC_INFORMATION, 0x00)
        self.assertEqual(dt.TRACK_RESOURCES_INFORMATION, 0x01)
        self.assertEqual(dt.POW_RESOURCES_DISC_INFORMATION, 0x02)
        self.assertEqual(ReadDiscInformation.DISC_STATUS.FINALIZED_DISC, 0x02)

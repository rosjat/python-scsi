# coding: utf-8

# Copyright (C) 2026 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_cdb_modesense10 import ModeSelect10
from pyscsi.pyscsi.scsi_enum_command import sbc
from pyscsi.utils.converter import scsi_ba_to_int
from tests.mock_device import MockDevice, MockSCSI


class CdbModeSelect10Test(unittest.TestCase):
    def test_main(self):
        data = {
            "medium_type": 0,
            "device_specific_parameter": 0,
            "mode_pages": [],
        }

        with MockSCSI(MockDevice(sbc)) as s:
            m = s.modeselect10(data)
            cdb = m.cdb

            self.assertEqual(cdb[0], s.device.opcodes.MODE_SELECT_10.value)
            self.assertEqual(cdb[1], 0x10)  # pf=1, sp=0
            self.assertEqual(scsi_ba_to_int(cdb[7:9]), len(m.dataout))
            self.assertEqual(len(cdb), 10)

            d = m.unmarshall_cdb(cdb)
            self.assertEqual(d["opcode"], s.device.opcodes.MODE_SELECT_10.value)
            self.assertEqual(d["pf"], 1)
            self.assertEqual(d["sp"], 0)
            self.assertEqual(d["parameter_list_length"], len(m.dataout))

            self.assertEqual(
                ModeSelect10.unmarshall_cdb(ModeSelect10.marshall_cdb(d)), d
            )

    def test_sp_and_pf_are_passed_through(self):
        data = {
            "medium_type": 0,
            "device_specific_parameter": 0,
            "mode_pages": [],
        }

        with MockSCSI(MockDevice(sbc)) as s:
            m = s.modeselect10(data, pf=0, sp=1)
            d = m.unmarshall_cdb(m.cdb)
            self.assertEqual(d["pf"], 0)
            self.assertEqual(d["sp"], 1)


if __name__ == "__main__":
    unittest.main()

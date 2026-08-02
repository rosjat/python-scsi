# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg <ronniesahlberg@gmail.com>
# Copyright (C) 2015 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_cdb_report_priority import ReportPriority
from pyscsi.pyscsi.scsi_enum_command import spc
from pyscsi.utils.converter import scsi_ba_to_int
from tests.mock_device import MockDevice, MockSCSI


class CdbReportpriorityTest(unittest.TestCase):
    def test_main(self) -> None:
        with MockSCSI(MockDevice(spc)) as s:
            r = s.reportpriority(priority=0x00, alloclen=1112527)
            raw_cdb = r.cdb
            self.assertEqual(raw_cdb[0], s.device.opcodes.SPC_OPCODE_A3.value)
            self.assertEqual(
                raw_cdb[1], s.device.opcodes.SPC_OPCODE_A3.serviceaction.REPORT_PRIORITY
            )
            self.assertEqual(raw_cdb[2], 0)
            self.assertEqual(scsi_ba_to_int(raw_cdb[6:10]), 1112527)
            self.assertEqual(raw_cdb[10:12], bytearray(2))
            cdb = r.unmarshall_cdb(raw_cdb)
            self.assertEqual(cdb["opcode"], s.device.opcodes.SPC_OPCODE_A3.value)
            self.assertEqual(
                cdb["service_action"],
                s.device.opcodes.SPC_OPCODE_A3.serviceaction.REPORT_PRIORITY,
            )
            self.assertEqual(cdb["priority_reported"], 0)
            self.assertEqual(cdb["alloc_len"], 1112527)

            d = ReportPriority.unmarshall_cdb(ReportPriority.marshall_cdb(cdb))
            self.assertEqual(d, cdb)

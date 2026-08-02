# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg <ronniesahlberg@gmail.com>
# Copyright (C) 2015 by Markus Rosjat <markus.rosjat@gmail.com>
# Copyright (C) 2023 by Brian Meagher <brian.meagher@ixsystems.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_cdb_report_target_port_groups import ReportTargetPortGroups
from pyscsi.pyscsi.scsi_enum_command import spc
from pyscsi.pyscsi.scsi_enum_report_target_port_groups import DATA_FORMAT_TYPE
from pyscsi.utils.converter import scsi_ba_to_int
from tests.mock_device import MockDevice, MockSCSI


class CdbReporttargetportgroupsTest(unittest.TestCase):
    def test_main(self) -> None:
        with MockSCSI(MockDevice(spc)) as s:
            r = s.reporttargetportgroups(data_format=0x00, alloclen=1112527)
            raw_cdb = r.cdb
            self.assertEqual(raw_cdb[0], s.device.opcodes.SPC_OPCODE_A3.value)
            self.assertEqual(
                raw_cdb[1] & 0x1F,
                s.device.opcodes.SPC_OPCODE_A3.serviceaction.REPORT_TARGET_PORT_GROUPS,
            )
            self.assertEqual(raw_cdb[1] & 0xE0, 0x00)
            self.assertEqual(raw_cdb[2:6], bytearray(4))
            self.assertEqual(scsi_ba_to_int(raw_cdb[6:10]), 1112527)
            self.assertEqual(raw_cdb[10:12], bytearray(2))
            cdb = r.unmarshall_cdb(raw_cdb)
            self.assertEqual(cdb["opcode"], s.device.opcodes.SPC_OPCODE_A3.value)
            self.assertEqual(
                cdb["service_action"],
                s.device.opcodes.SPC_OPCODE_A3.serviceaction.REPORT_TARGET_PORT_GROUPS,
            )
            self.assertEqual(cdb["parameter_data_format"], 0)
            self.assertEqual(cdb["alloc_len"], 1112527)

            d = ReportTargetPortGroups.unmarshall_cdb(
                ReportTargetPortGroups.marshall_cdb(cdb)
            )
            self.assertEqual(d, cdb)

            r = s.reporttargetportgroups(data_format=0x01, alloclen=0x400)
            raw_cdb = r.cdb
            self.assertEqual(raw_cdb[0], s.device.opcodes.SPC_OPCODE_A3.value)
            self.assertEqual(
                raw_cdb[1] & 0x1F,
                s.device.opcodes.SPC_OPCODE_A3.serviceaction.REPORT_TARGET_PORT_GROUPS,
            )
            self.assertEqual(raw_cdb[1] & 0xE0, 0x20)
            self.assertEqual(raw_cdb[2:6], bytearray(4))
            self.assertEqual(scsi_ba_to_int(raw_cdb[6:10]), 0x400)
            self.assertEqual(raw_cdb[10:12], bytearray(2))
            cdb = r.unmarshall_cdb(raw_cdb)
            self.assertEqual(cdb["opcode"], s.device.opcodes.SPC_OPCODE_A3.value)
            self.assertEqual(
                cdb["service_action"],
                s.device.opcodes.SPC_OPCODE_A3.serviceaction.REPORT_TARGET_PORT_GROUPS,
            )
            self.assertEqual(
                cdb["parameter_data_format"],
                DATA_FORMAT_TYPE.EXTENDED_HEADER_PARAMETER_DATA_FORMAT,
            )
            self.assertEqual(cdb["alloc_len"], 0x400)

            d = ReportTargetPortGroups.unmarshall_cdb(
                ReportTargetPortGroups.marshall_cdb(cdb)
            )
            self.assertEqual(d, cdb)

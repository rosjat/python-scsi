# coding: utf-8

# Copyright (C) 2026 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_cdb_report_target_port_groups import ReportTargetPortGroups
from pyscsi.utils.converter import scsi_ba_to_int

# SPC-3 r23 table 163, REPORT TARGET PORT GROUPS parameter data format:
#
#   bytes 0-3   RETURN DATA LENGTH (n-3)
#   bytes 4-n   target port group descriptors
#
# Table 164, target port group descriptor:
#
#   byte  0     PREF (7) | reserved | ASYMMETRIC ACCESS STATE (3-0)
#   byte  1     T_SUP (7) | O_SUP (6) | ... | U_SUP (3) | S_SUP (2) |
#               AN_SUP (1) | AO_SUP (0)
#   bytes 2-3   TARGET PORT GROUP
#   byte  5     STATUS CODE
#   byte  6     vendor specific
#   byte  7     TARGET PORT COUNT
#   bytes 8-n   target port descriptors, 4 bytes each (table 167), the
#               RELATIVE TARGET PORT IDENTIFIER in bytes 2-3 of each

# Captured verbatim from scsi_debug. sg_rtpg reads it as two target port
# groups: 0x200 (aas 0x00, one port 0x01) and 0x280 (aas 0x03, one port 0x02).
DEVICE_RESPONSE = bytearray.fromhex(
    "00000018" "00010200" "00000001" "00000001" "03080280" "00000001" "00000002"
)


class ReportTargetPortGroupsDatain(unittest.TestCase):
    def test_matches_the_device(self) -> None:
        self.assertEqual(scsi_ba_to_int(DEVICE_RESPONSE[:4]), 24)

        r = ReportTargetPortGroups.unmarshall_datain(DEVICE_RESPONSE)
        groups = r["target_port_group_descriptors"]
        self.assertEqual(len(groups), 2)

        self.assertEqual(groups[0]["target_port_group"], 0x0200)
        self.assertEqual(groups[0]["asymmetric_access_state"], 0x00)
        self.assertEqual(groups[0]["target_port_count"], 1)
        self.assertEqual(groups[0]["target_ports"][0]["relative_target_port_id"], 1)

        self.assertEqual(groups[1]["target_port_group"], 0x0280)
        self.assertEqual(groups[1]["asymmetric_access_state"], 0x03)
        self.assertEqual(groups[1]["target_port_count"], 1)
        self.assertEqual(groups[1]["target_ports"][0]["relative_target_port_id"], 2)

    def test_support_bits(self) -> None:
        r = ReportTargetPortGroups.unmarshall_datain(DEVICE_RESPONSE)
        groups = r["target_port_group_descriptors"]
        # byte 1 of the first descriptor is 0x01 -> AO_SUP only
        self.assertEqual(groups[0]["ao_sup"], 1)
        self.assertEqual(groups[0]["u_sup"], 0)
        # byte 1 of the second is 0x08 -> U_SUP only
        self.assertEqual(groups[1]["u_sup"], 1)
        self.assertEqual(groups[1]["ao_sup"], 0)


class ReportTargetPortGroupsMarshall(unittest.TestCase):
    def test_round_trip_of_the_device_response(self) -> None:
        parsed = ReportTargetPortGroups.unmarshall_datain(DEVICE_RESPONSE)
        self.assertEqual(
            ReportTargetPortGroups.marshall_datain(parsed), DEVICE_RESPONSE
        )


if __name__ == "__main__":
    unittest.main()

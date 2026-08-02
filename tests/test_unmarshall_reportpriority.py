# coding: utf-8

# Copyright (C) 2026 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest
from typing import List

from pyscsi.pyscsi.scsi_cdb_report_priority import ReportPriority
from pyscsi.pyscsi.scsi_enum_persistentreserve import PROTOCOL_ID
from pyscsi.pyscsi.scsi_transport_id import marshall_transport_id
from pyscsi.utils.converter import scsi_int_to_ba

# SPC-3 r23 table 152, REPORT PRIORITY parameter data format:
#
#   bytes 0-3   PRIORITY PARAMETER DATA LENGTH (n-3)
#   bytes 4-n   priority descriptors
#
# "The PRIORITY PARAMETER DATA LENGTH field indicates the number of bytes of
# parameter data that follow."
#
# Table 153, priority descriptor format:
#
#   byte  0     reserved (7-4) | CURRENT PRIORITY (3-0)
#   byte  1     reserved
#   bytes 2-3   RELATIVE TARGET PORT IDENTIFIER
#   bytes 4-5   reserved
#   bytes 6-7   ADDITIONAL DESCRIPTOR LENGTH (n-7), "the size of the TransportID"
#   bytes 8-n   TRANSPORTID


SAS_ADDR = bytearray(b"\x50\x01\x02\x03\x04\x05\x06\x07")


def descriptor(priority: int, rtpi: int, transport_id: bytearray) -> bytearray:
    d = bytearray(8)
    d[0] = priority & 0x0F
    d[2:4] = scsi_int_to_ba(rtpi, 2)
    d[6:8] = scsi_int_to_ba(len(transport_id), 2)
    return d + transport_id


def parameter_data(descriptors: List[bytearray]) -> bytearray:
    body = bytearray()
    for d in descriptors:
        body += d
    return scsi_int_to_ba(len(body), 4) + body


class ReportPriorityDatain(unittest.TestCase):
    def test_single_descriptor(self) -> None:
        tid = marshall_transport_id(
            {"tpid_format": 0, "protocol_id": PROTOCOL_ID.SAS, "sas_address": SAS_ADDR}
        )
        data = parameter_data([descriptor(priority=3, rtpi=0x0102, transport_id=tid)])

        result = ReportPriority.unmarshall_datain(data)

        self.assertEqual(len(result["priority_descriptors"]), 1)
        d = result["priority_descriptors"][0]
        self.assertEqual(d["current_priority"], 3)
        self.assertEqual(d["rtpi"], 0x0102)
        self.assertEqual(d["adlen"], len(tid))
        # A TransportID decodes to the same structure the other commands
        # return for one, not to an opaque blob.
        self.assertEqual(d["transport_id"]["protocol_id"], PROTOCOL_ID.SAS)
        self.assertEqual(d["transport_id"]["sas_address"], SAS_ADDR)

    def test_multiple_descriptors(self) -> None:
        tid = marshall_transport_id(
            {"tpid_format": 0, "protocol_id": PROTOCOL_ID.SAS, "sas_address": SAS_ADDR}
        )
        data = parameter_data([descriptor(1, 0x0001, tid), descriptor(2, 0x0002, tid)])
        result = ReportPriority.unmarshall_datain(data)
        self.assertEqual(len(result["priority_descriptors"]), 2)
        self.assertEqual(result["priority_descriptors"][1]["rtpi"], 0x0002)

    def test_last_transport_id_is_complete(self) -> None:
        """
        The descriptor slice must end at 4 + LENGTH, not LENGTH. Four bytes
        short, the final TransportID is truncated -- the descriptor count stays
        right, so only a field near the end of the structure reveals it. RDMA
        puts INITIATOR PORT IDENTIFIER at bytes 8-23, which is exactly where
        the shortfall lands.
        """
        port_id = bytearray(range(0x10, 0x20))
        tid = marshall_transport_id(
            {
                "tpid_format": 0,
                "protocol_id": PROTOCOL_ID.RDMA,
                "initiator_port_identifier": port_id,
            }
        )
        data = parameter_data([descriptor(priority=1, rtpi=0x0001, transport_id=tid)])

        result = ReportPriority.unmarshall_datain(data)
        d = result["priority_descriptors"][0]
        self.assertEqual(d["adlen"], len(tid))
        self.assertEqual(d["transport_id"]["initiator_port_identifier"], port_id)

    def test_empty_parameter_data(self) -> None:
        """No descriptors: the loop never runs, so nothing breaks."""
        result = ReportPriority.unmarshall_datain(parameter_data([]))
        self.assertEqual(result["priority_descriptors"], [])


class ReportPriorityMarshall(unittest.TestCase):
    def test_length_counts_the_bytes_that_follow(self) -> None:
        self.assertEqual(
            bytearray(ReportPriority.marshall_datain({})),
            bytearray(b"\x00\x00\x00\x00"),
        )

    def test_round_trip(self) -> None:
        source = {
            "priority_descriptors": [
                {
                    "current_priority": 3,
                    "rtpi": 0x0102,
                    "adlen": 24,
                    "transport_id": {
                        "tpid_format": 0,
                        "protocol_id": PROTOCOL_ID.SAS,
                        "sas_address": SAS_ADDR,
                    },
                }
            ]
        }
        self.assertEqual(
            ReportPriority.unmarshall_datain(ReportPriority.marshall_datain(source)),
            source,
        )


if __name__ == "__main__":
    unittest.main()

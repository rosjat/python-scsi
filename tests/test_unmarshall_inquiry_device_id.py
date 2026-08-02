# coding: utf-8

# Copyright (C) 2026 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_cdb_inquiry import Inquiry

# INQUIRY VPD page 83h, Device Identification (SPC-3 r23 7.6.3).
#
# Captured verbatim from scsi_debug. sg_inq reads it as seven designation
# descriptors: T10 vendor identification, NAA, relative target port, NAA,
# target port group, NAA, and a SCSI name string.
DEVICE_RESPONSE = bytearray.fromhex(
    "00830070"
    "0201001c4c696e7578202020736373695f64656275672020202020203430303030"[:-2]
    + "010300083333333000000fa0"
    + "6194000400000001"
    + "619300083222222000000f9e"
    + "6195000400000200"
    + "61a300083222222000000f9d"
    + "63a800186e61612e3332323232323230303030303046394400000000"
)


class InquiryDeviceIdentification(unittest.TestCase):
    def setUp(self) -> None:
        parsed = Inquiry.unmarshall_datain(DEVICE_RESPONSE, evpd=1)
        # None only for a page code with no branch; this one is DEVICE_IDENTIFICATION.
        assert parsed is not None
        self.parsed = parsed

    def test_all_designators_are_parsed(self) -> None:
        self.assertEqual(len(self.parsed["designator_descriptors"]), 7)
        self.assertEqual(
            [d["designator_type"] for d in self.parsed["designator_descriptors"]],
            [1, 3, 4, 3, 5, 3, 8],
        )

    def test_values_match_sg_inq(self) -> None:
        d = self.parsed["designator_descriptors"]
        # sg_inq prints the whole 64-bit NAA name as [0x3333333000000fa0].
        # NAA occupies the top four bits, so the field below it is 60 bits.
        self.assertEqual(d[1]["designator"]["naa"], 3)
        self.assertEqual(
            d[1]["designator"]["locally_administered_value"], 0x333333000000FA0
        )
        combined = (d[1]["designator"]["naa"] << 60) | d[1]["designator"][
            "locally_administered_value"
        ]
        self.assertEqual(combined, 0x3333333000000FA0)
        # relative target port 0x1, target port group 0x200
        self.assertEqual(d[2]["designator"]["relative_port"], 1)
        self.assertEqual(d[4]["designator"]["target_portal_group"], 0x200)
        # SCSI name string is UTF-8 text
        self.assertTrue(
            bytes(d[6]["designator"]["scsi_name_string"]).startswith(b"naa.")
        )

    def test_round_trip_reproduces_the_device_bytes(self) -> None:
        """
        Every designator, including the SCSI name string, must marshall back to
        exactly what the device sent.
        """
        self.assertEqual(
            bytearray(Inquiry.marshall_datain(self.parsed)), DEVICE_RESPONSE
        )

    def test_scsi_name_string_designator_marshalls(self) -> None:
        """
        marshall_designator returned the literal key name in a list for this
        type, so any page carrying one raised TypeError on concat.
        """
        descriptor = self.parsed["designator_descriptors"][6]
        out = Inquiry.marshall_designation_descriptor(descriptor)
        self.assertEqual(
            bytes(out[4:]), bytes(descriptor["designator"]["scsi_name_string"])
        )


class InquiryAtaInformation(unittest.TestCase):
    """
    INQUIRY VPD page 89h, ATA Information (SAT).

    Header of a scsi_debug response. sg_vpd reads the three SAT fields as
    'linux   ', 'SAT scsi_debug  ' and '1234'.
    """

    HEADER = bytearray.fromhex(
        "00890238"
        "00000000"
        "6c696e7578202020"
        "53415420736373695f64656275672020"
        "31323334"
    )

    def test_sat_fields_do_not_overlap(self) -> None:
        data = self.HEADER + bytearray(572 - len(self.HEADER))
        r = Inquiry.unmarshall_datain(data, evpd=1)
        assert r is not None

        self.assertEqual(bytes(r["sat_vendor_identification"]), b"linux   ")
        # 16 bytes at offset 16; a longer read swallows the revision level,
        # which starts at 32.
        self.assertEqual(bytes(r["sat_product_identification"]), b"SAT scsi_debug  ")
        self.assertEqual(bytes(r["sat_product_rev_lvl"]), b"1234")


if __name__ == "__main__":
    unittest.main()

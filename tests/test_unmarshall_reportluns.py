# coding: utf-8

# Copyright (C) 2026 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import unittest

from pyscsi.pyscsi.scsi_cdb_report_luns import ReportLuns
from pyscsi.utils.converter import scsi_ba_to_int, scsi_int_to_ba

# SPC-3 r23 table 149, REPORT LUNS parameter data format:
#
#   bytes 0-3   LUN LIST LENGTH (n-7)
#   bytes 4-7   reserved
#   bytes 8-n   the LUN list, one 8-byte LUN per entry
#
# "The LUN LIST LENGTH field shall contain the length in bytes of the LUN list
# that is available to be transferred. The LUN list length is the number of
# logical unit numbers in the logical unit inventory multiplied by eight."
#
# So the field counts only the list, not the 8-byte header.


def conformant_parameter_data(luns):
    """Build REPORT LUNS parameter data exactly as a device would return it."""
    data = bytearray(8)
    for lun in luns:
        data += scsi_int_to_ba(lun, 8)
    data[:4] = scsi_int_to_ba(len(luns) * 8, 4)
    return data


class ReportLunsRoundTrip(unittest.TestCase):
    """
    The round-trip this package asserts elsewhere: a dict marshalled to bytes
    and unmarshalled back. This passes today -- the two length errors below
    cancel out, which is why they went unnoticed.
    """

    def test_lun_values_survive_a_round_trip(self):
        for count in (1, 2, 3):
            with self.subTest(luns=count):
                source = {"luns": [{"lun": n} for n in range(count)]}
                result = ReportLuns.unmarshall_datain(
                    ReportLuns.marshall_datain(source)
                )
                self.assertEqual(len(result["luns"]), count)
                for n in range(count):
                    self.assertEqual(result["luns"][n]["lun%d" % n], n)

    def test_unmarshall_renames_lun_to_lun_n(self):
        """
        marshall_datain reads 'lun'; unmarshall_datain emits 'lun0', 'lun1'.
        Pinning the asymmetry rather than judging it -- the source comment
        calls the per-LUN dict into question, so this is a design decision,
        not a defect.
        """
        result = ReportLuns.unmarshall_datain(
            ReportLuns.marshall_datain({"luns": [{"lun": 7}]})
        )
        self.assertEqual(result["luns"], [{"lun0": 7}])


class ReportLunsSpecConformance(unittest.TestCase):
    """
    Against buffers built to table 149, i.e. what a real device sends.
    """

    def test_empty_list(self):
        result = ReportLuns.unmarshall_datain(conformant_parameter_data([]))
        self.assertEqual(result["luns"], [])

    def test_lun_count_is_right(self):
        """The number of entries is correct; only the last value is wrong."""
        for count in (1, 2, 3):
            with self.subTest(luns=count):
                data = conformant_parameter_data(list(range(1, count + 1)))
                result = ReportLuns.unmarshall_datain(data)
                self.assertEqual(len(result["luns"]), count)

    def test_last_lun_is_decoded_from_all_eight_bytes(self):
        # One LUN, deliberately non-zero: the single-LUN case is affected too.
        result = ReportLuns.unmarshall_datain(conformant_parameter_data([5]))
        self.assertEqual(result["luns"][0]["lun0"], 5)

    def test_every_lun_of_a_conformant_buffer_is_decoded(self):
        data = conformant_parameter_data([0x01, 0x02, 0x03])
        result = ReportLuns.unmarshall_datain(data)
        self.assertEqual(
            [list(e.values())[0] for e in result["luns"]], [0x01, 0x02, 0x03]
        )

    def test_lun_list_length_counts_only_the_list(self):
        # An empty inventory must report 0; SELECT REPORT 00h in table 148 says
        # "If there are no logical units, the LUN LIST LENGTH field shall be
        # zero."
        self.assertEqual(scsi_ba_to_int(ReportLuns.marshall_datain({})[:4]), 0)

        two = ReportLuns.marshall_datain({"luns": [{"lun": 0}, {"lun": 1}]})
        self.assertEqual(scsi_ba_to_int(two[:4]), 16)


if __name__ == "__main__":
    unittest.main()

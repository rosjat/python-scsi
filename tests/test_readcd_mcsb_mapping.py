# coding: utf-8

# Copyright (C) 2026 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""
READ CD main channel selection, checked against MMC-6 r02g table 354
("Main Channel Selection and Mapped Values"). The same four rows appear
unchanged in MMC-4, so this is not a revision difference.

unmarshall_datain applies the mapping and then includes one field per bit of
the mapped value, so the mapping is observable from the result alone:

    sync             <- 80h      sector-header    <- 20h
    sector-subheader <- 40h      data             <- 10h
    edc              <- 08h
"""

import unittest

from pyscsi.pyscsi.scsi_cdb_readcd import ReadCd
from pyscsi.pyscsi.scsi_enum_readcd import EXPECTED_SECTOR_TYPE

# mcsb -> (CD-DA, Mode 1, Mode 2 Formless, Mode 2 Form 1, Mode 2 Form 2)
# "X" is Invalid in the table.
TABLE_354 = {
    0x00: (0x00, 0x00, 0x00, 0x00, 0x00),
    0x08: (0x10, 0x08, 0x10, 0x08, 0x08),
    0x10: (0x10, 0x10, 0x10, 0x10, 0x10),
    0x18: (0x10, 0x18, 0x10, 0x18, 0x18),
    0x20: (0x10, 0x20, 0x20, 0x20, 0x20),
    0x28: (0x10, "X", "X", "X", "X"),
    0x30: (0x10, 0x30, 0x30, "X", "X"),
    0x38: (0x10, 0x38, 0x30, "X", "X"),
    0x40: (0x10, 0x00, 0x00, 0x40, 0x40),
    0x48: (0x10, "X", "X", "X", "X"),
    0x50: (0x10, 0x10, 0x10, 0x50, 0x50),
    0x58: (0x10, 0x18, 0x10, 0x58, 0x58),
    0x60: (0x10, 0x20, 0x20, 0x60, 0x60),
    0x68: (0x10, "X", "X", "X", "X"),
    0x70: (0x10, 0x30, 0x30, 0x70, 0x70),
    0x78: (0x10, 0x38, 0x38, 0x78, 0x78),
    0x80: (0x10, 0x80, 0x80, 0x80, 0x80),
    0x88: (0x10, "X", "X", "X", "X"),
    0x90: (0x10, "X", "X", "X", "X"),
    0x98: (0x10, "X", "X", "X", "X"),
    0xA0: (0x10, 0xA0, 0xA0, 0xA0, 0xA0),
    0xA8: (0x10, "X", "X", "X", "X"),
    0xB0: (0x10, 0xB0, 0xB0, "X", "X"),
    0xB8: (0x10, 0xB8, 0xB0, "X", "X"),
    0xC0: (0x10, "X", "X", "X", "X"),
    0xC8: (0x10, "X", "X", "X", "X"),
    0xD0: (0x10, "X", "X", "X", "X"),
    0xD8: (0x10, "X", "X", "X", "X"),
    0xE0: (0x10, 0xA0, 0xA0, 0xE0, 0xE0),
    0xE8: (0x10, "X", "X", "X", "X"),
    0xF0: (0x10, 0xB0, 0xB0, 0xF0, 0xF0),
    0xF8: (0x10, 0xB8, 0xB0, 0xF8, 0xF8),
}

SECTOR_TYPES = (
    ("CD-DA", EXPECTED_SECTOR_TYPE.CDDA),
    ("Mode 1", EXPECTED_SECTOR_TYPE.MODE_1),
    ("Mode 2 Formless", EXPECTED_SECTOR_TYPE.MODE_2_FORMLESS),
    ("Mode 2 Form 1", EXPECTED_SECTOR_TYPE.MODE_2_FORM_1),
    ("Mode 2 Form 2", EXPECTED_SECTOR_TYPE.MODE_2_FORM_2),
)

# The cells where the implementation and the table disagree. Two of them are a
# single swap (08h has Form 1 and Formless the wrong way round), so these six
# cells are three transcription slips in a 160-cell table.
KNOWN_DEVIATIONS = {
    (0x00, EXPECTED_SECTOR_TYPE.CDDA),
    (0x08, EXPECTED_SECTOR_TYPE.MODE_2_FORMLESS),
    (0x08, EXPECTED_SECTOR_TYPE.MODE_2_FORM_1),
    (0x18, EXPECTED_SECTOR_TYPE.MODE_2_FORMLESS),
    (0x38, EXPECTED_SECTOR_TYPE.MODE_2_FORM_1),
    (0x38, EXPECTED_SECTOR_TYPE.MODE_2_FORM_2),
}

BIT_FOR_KEY = (
    ("sync", 0x80),
    ("sector-subheader", 0x40),
    ("sector-header", 0x20),
    ("data", 0x10),
    ("edc", 0x08),
)


def effective_mcsb(mcsb, est):
    """
    Run one sector through unmarshall_datain and rebuild the mapped MCSB from
    the fields it returned. Returns "X" if the call was rejected.
    """
    try:
        result = ReadCd.unmarshall_datain(
            bytearray(4096), lba=0, tl=1, est=est, mcsb=mcsb >> 3, c2ei=0, scsb=0
        )
    except ValueError as exc:
        if "Invalid MCSB/EST" in str(exc):
            return "X"
        # Anything else is the sector parser declining to build a field after
        # the mapping already happened -- e.g. "No EDC/ECC for Mode2Formless".
        # That says nothing about the mapping, so it is not a table result.
        return "parser-declined"
    except NotImplementedError:
        return "parser-declined"

    # unmarshall_datain keys the result by LBA.
    sector = result[0]
    value = 0
    for key, bit in BIT_FOR_KEY:
        if key in sector:
            value |= bit
    return value


class ReadCdMainChannelSelection(unittest.TestCase):
    def test_table_354_is_transcribed_completely(self):
        self.assertEqual(len(TABLE_354), 32)
        self.assertEqual(sum(len(v) for v in TABLE_354.values()), 160)

    def test_mapping_matches_mmc_table_354(self):
        deviations = []
        for mcsb in sorted(TABLE_354):
            for idx, (name, est) in enumerate(SECTOR_TYPES):
                if (mcsb, est) in KNOWN_DEVIATIONS:
                    continue
                want = TABLE_354[mcsb][idx]
                with self.subTest(mcsb="0x%02X" % mcsb, sector_type=name):
                    got = effective_mcsb(mcsb, est)
                    if got == "parser-declined":
                        continue
                    self.assertEqual(got, want)
        self.assertEqual(deviations, [])

    @unittest.expectedFailure
    def test_known_deviations_from_table_354(self):
        """
        Six cells of table 354 are transcribed differently in the if-chain:

          00h / CD-DA          maps to 10h, but the table reads 00h in every
                               column and the prose exempts "no fields"
          08h                  Mode 2 Form 1 and Formless are swapped
          18h / Formless       the 10h mapping is missing
          38h                  absent from the invalid list for Form 1 and 2

        MMC-4 carries the same four rows, so this is not a revision
        difference. Left as-is deliberately: 154 of 160 cells are correct and
        no optical drive is available to confirm against hardware.
        """
        for mcsb, est in sorted(KNOWN_DEVIATIONS):
            idx = [e for _, e in SECTOR_TYPES].index(est)
            self.assertEqual(effective_mcsb(mcsb, est), TABLE_354[mcsb][idx])


if __name__ == "__main__":
    unittest.main()

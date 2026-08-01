# coding: utf-8

# Copyright (C) 2026 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""
Key validation in the EXTENDED COPY parameter builders.

Each builder checks that the caller supplied no unknown keys, then names the
offending one in the error.
"""

import unittest

from pyscsi.pyscsi.scsi_cdb_extended_copy_spc4 import ExtendedCopy as ExtendedCopySpc4
from pyscsi.pyscsi.scsi_cdb_extended_copy_spc5 import ExtendedCopy as ExtendedCopySpc5

BOGUS = "not_a_real_field"

# SPC-5 renamed "target descriptor" to "CSCD descriptor"; both modules follow
# their own standard, so the key names differ.
CASES = (
    (ExtendedCopySpc4, "target"),
    (ExtendedCopySpc5, "cscd"),
)


def block_to_block_segment(kind):
    return {
        "descriptor_type_code": 0x02,
        "source_%s_descriptor_id" % kind: 0,
        "destination_%s_descriptor_id" % kind: 1,
        "block_device_number_of_blocks": 8,
        "source_block_device_logical_block_address": 0,
        "destination_block_device_logical_block_address": 0,
    }


class SegmentKeyValidation(unittest.TestCase):
    def test_valid_segment_marshalls(self):
        for cls, kind in CASES:
            with self.subTest(spc=cls.__module__[-4:]):
                out = cls.marshall_segment(block_to_block_segment(kind))
                self.assertEqual(len(out), 28)

    def test_unknown_key_is_rejected(self):
        for cls, kind in CASES:
            with self.subTest(spc=cls.__module__[-4:]):
                segment = block_to_block_segment(kind)
                segment[BOGUS] = 1
                with self.assertRaises(ValueError):
                    cls.marshall_segment(segment)

    def test_the_rejected_key_is_named(self):
        """The message must identify the key that is actually invalid."""
        for cls, kind in CASES:
            segment = block_to_block_segment(kind)
            segment[BOGUS] = 1
            with self.assertRaises(ValueError) as caught:
                cls.marshall_segment(segment)
            self.assertIn(BOGUS, str(caught.exception))


if __name__ == "__main__":
    unittest.main()

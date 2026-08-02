# coding: utf-8

# Copyright (C) 2026 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""
Every segment descriptor type code marshall_segment claims to implement.

Type codes 01h and 0Ch (copy stream to block) reached for
_segment_descriptor_bits_stream_block, which is not the name of any attribute
-- the layout is _segment_descriptor_bits_stream_to_block -- so both raised
AttributeError instead of building a descriptor.
"""

import unittest
from typing import Any, Dict, Iterator, Tuple

from pyscsi.pyscsi.scsi_cdb_extended_copy_spc4 import ExtendedCopy as ExtendedCopySpc4
from pyscsi.pyscsi.scsi_cdb_extended_copy_spc5 import ExtendedCopy as ExtendedCopySpc5

# SPC-4 names the endpoints "target descriptors"; SPC-5 renamed them CSCDs.
SPC4_IDS = {
    "source_target_descriptor_id": 0,
    "destination_target_descriptor_id": 1,
}
SPC5_IDS = {
    "source_cscd_descriptor_id": 0,
    "destination_cscd_descriptor_id": 1,
}

STREAM_FIELDS = {
    "cat": 0,
    "stream_device_transfer_length": 1,
    "block_device_number_of_blocks": 1,
    "block_device_logical_block_address": 0,
}

BLOCK_FIELDS = {
    "cat": 0,
    "dc": 0,
    "block_device_number_of_blocks": 1,
    "source_block_device_logical_block_address": 0,
    "destination_block_device_logical_block_address": 0,
}

# type code -> (extra fields, encoded length)
BLOCK_TO_STREAM = (0x00, 0x0B)
STREAM_TO_BLOCK = (0x01, 0x0C)
BLOCK_TO_BLOCK = (0x02, 0x0D)


class SegmentDescriptorTypes(unittest.TestCase):
    def _cases(
        self, cls: Any, ids: Dict[str, int], block_extra: Dict[str, int]
    ) -> Iterator[Tuple[int, Dict[str, int], int]]:
        for code in BLOCK_TO_STREAM + STREAM_TO_BLOCK:
            yield code, dict(ids, **STREAM_FIELDS), 24
        for code in BLOCK_TO_BLOCK:
            yield code, dict(ids, **block_extra), 28

    def _check(
        self, cls: Any, ids: Dict[str, int], block_extra: Dict[str, int]
    ) -> None:
        for code, fields, length in self._cases(cls, ids, block_extra):
            with self.subTest(code=hex(code)):
                seg = dict(fields, descriptor_type_code=code)
                result = cls.marshall_segment(seg)
                self.assertEqual(len(result), length)
                # byte 0 is the type code, bytes 2-3 the descriptor length
                self.assertEqual(result[0], code)
                self.assertEqual(result[3], length - 4)

    def test_spc4_every_implemented_type_code(self) -> None:
        self._check(ExtendedCopySpc4, SPC4_IDS, BLOCK_FIELDS)

    def test_spc5_every_implemented_type_code(self) -> None:
        fields = dict(BLOCK_FIELDS, fco=0)
        self._check(ExtendedCopySpc5, SPC5_IDS, fields)

    def test_unimplemented_type_code_still_raises(self) -> None:
        for cls, ids in ((ExtendedCopySpc4, SPC4_IDS), (ExtendedCopySpc5, SPC5_IDS)):
            with self.subTest(cls=cls.__module__):
                with self.assertRaises(NotImplementedError):
                    cls.marshall_segment(dict(ids, descriptor_type_code=0x03))


if __name__ == "__main__":
    unittest.main()

# coding: utf-8

# Copyright (C) 2026 by Markus Rosjat <markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""
WRITE SAME (16) with NDOB set.

SBC-3 5.48: an NDOB bit set to one means no data-out buffer is transferred and
the logical block data comes from the device server, so WriteSame16 sets
dataout to None. A transport must cope with that.
"""

import unittest

from pyscsi.pyscsi.scsi_cdb_writesame16 import WriteSame16
from pyscsi.pyscsi.scsi_enum_command import sbc


class WriteSame16Ndob(unittest.TestCase):
    def test_ndob_leaves_no_dataout(self) -> None:
        cmd = WriteSame16(
            sbc.WRITE_SAME_16, blocksize=0, lba=0, nb=1, data=None, ndob=1
        )
        self.assertIsNone(cmd.dataout)
        d = cmd.unmarshall_cdb(cmd.cdb)
        self.assertEqual(d["ndob"], 1)

    def test_without_ndob_there_is_a_dataout_buffer(self) -> None:
        cmd = WriteSame16(
            sbc.WRITE_SAME_16,
            blocksize=512,
            lba=0,
            nb=1,
            data=bytearray(512),
            ndob=0,
        )
        assert cmd.dataout is not None
        self.assertEqual(len(cmd.dataout), 512)
        d = cmd.unmarshall_cdb(cmd.cdb)
        self.assertEqual(d["ndob"], 0)

    def test_a_none_dataout_is_falsy_not_an_error(self) -> None:
        """
        ISCSIDevice.execute sizes the transfer from the buffers. It used to ask
        len(cmd.dataout), which raises on the NDOB command; a truth test gives
        the same answer for a bytearray and tolerates None.
        """
        cmd = WriteSame16(
            sbc.WRITE_SAME_16, blocksize=0, lba=0, nb=1, data=None, ndob=1
        )
        self.assertFalse(cmd.dataout)
        with self.assertRaises(TypeError):
            # The TypeError is what this asserts, so the bad argument stands.
            len(cmd.dataout)  # type: ignore[arg-type]

        empty = bytearray(0)
        self.assertEqual(bool(empty), bool(len(empty)))


if __name__ == "__main__":
    unittest.main()

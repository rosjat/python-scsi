# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg<ronniesahlberg@gmail.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import TYPE_CHECKING

from pyscsi.pyscsi.scsi_command import SCSICommand

if TYPE_CHECKING:
    from pyscsi.pyscsi.scsi_opcode import OpCode

#
# SCSI WriteSame10 command and definitions
#


class WriteSame10(SCSICommand):
    """
    A class to send a WriteSame(10) command to a scsi device
    """

    _cdb_bits = {
        "opcode": [0xFF, 0],
        "wrprotect": [0xE0, 1],
        "anchor": [0x10, 1],
        "unmap": [0x08, 1],
        "lba": [0xFFFFFFFF, 2],
        "group": [0x1F, 6],
        "nb": [0xFFFF, 7],
    }

    def __init__(
        self,
        opcode: "OpCode",
        blocksize: int,
        lba: int,
        nb: int,
        data: bytearray,
        wrprotect: int = 0,
        anchor: int = 0,
        unmap: int = 0,
        group: int = 0,
    ) -> None:
        """
        initialize a new instance

        :param opcode: a OpCode instance
        :param blocksize: a blocksize
        :param lba: logical block address
        :param nb: number of logical blocks
        :param data: a byte array with data
        :param wrprotect: value to specify write protection information
        :param anchor: anchor can have a value of 0 or 1
        :param unmap: unmap can have a value of 0 or 1
        :param group: group number, can be 0 or greater
        """
        if blocksize == 0:
            raise SCSICommand.MissingBlocksizeException

        SCSICommand.__init__(self, opcode, blocksize, 0)
        self.dataout = data
        self.cdb = self.build_cdb(
            opcode=self.opcode.value,
            lba=lba,
            nb=nb,
            wrprotect=wrprotect,
            anchor=anchor,
            unmap=unmap,
            group=group,
        )

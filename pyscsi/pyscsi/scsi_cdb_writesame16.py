# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

# coding: utf-8


from typing import TYPE_CHECKING, Any, Dict, Optional

from pyscsi.pyscsi.scsi_command import SCSICommand

if TYPE_CHECKING:
    from pyscsi.pyscsi.scsi_opcode import OpCode

from pyscsi.utils.converter import decode_bits, encode_dict

#
# SCSI WriteSame16 command and definitions
#


class WriteSame16(SCSICommand[Dict[str, Any]]):
    """
    A class to send a WriteSame(16) command to a scsi device
    """

    _cdb_bits = {
        "opcode": [0xFF, 0],
        "wrprotect": [0xE0, 1],
        "anchor": [0x10, 1],
        "unmap": [0x08, 1],
        "ndob": [0x01, 1],
        "lba": [0xFFFFFFFFFFFFFFFF, 2],
        "group": [0x1F, 14],
        "nb": [0xFFFFFFFF, 10],
    }

    def __init__(
        self,
        opcode: "OpCode",
        blocksize: int,
        lba: int,
        nb: int,
        data: Optional[bytearray],
        wrprotect: int = 0,
        anchor: int = 0,
        unmap: int = 0,
        ndob: int = 0,
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
        :param ndob: Value can be 0 or 1, use logical block data from data out buffer
                     (data arg) if set to 1.
        :param group: group number, can be 0 or greater
        """
        if not ndob and blocksize == 0:
            raise SCSICommand.MissingBlocksizeException

        SCSICommand.__init__(self, opcode, 0 if ndob else blocksize, 0)
        self.dataout = None if ndob else data
        self.cdb = self.build_cdb(
            opcode=self.opcode.value,
            lba=lba,
            nb=nb,
            wrprotect=wrprotect,
            anchor=anchor,
            unmap=unmap,
            ndob=ndob,
            group=group,
        )

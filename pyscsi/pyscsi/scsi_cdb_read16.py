# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg<ronniesahlberg@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import TYPE_CHECKING, Any, Dict

from pyscsi.pyscsi.scsi_command import SCSICommand

if TYPE_CHECKING:
    from pyscsi.pyscsi.scsi_opcode import OpCode

#
# SCSI Read16 command and definitions
#


class Read16(SCSICommand[Dict[str, Any]]):
    """
    A class to send a Read(16) command to a scsi device
    """

    _cdb_bits = {
        "opcode": [0xFF, 0],
        "rdprotect": [0xE0, 1],
        "dpo": [0x10, 1],
        "fua": [0x08, 1],
        "rarc": [0x04, 1],
        "lba": [0xFFFFFFFFFFFFFFFF, 2],
        "group": [0x1F, 14],
        "tl": [0xFFFFFFFF, 10],
    }

    def __init__(
        self,
        opcode: "OpCode",
        blocksize: int,
        lba: int,
        tl: int,
        rdprotect: int = 0,
        dpo: int = 0,
        fua: int = 0,
        rarc: int = 0,
        group: int = 0,
    ) -> None:
        """
        initialize a new instance

        :param opcode: a OpCode instance
        :param blocksize: a blocksize
        :param lba: Logical Block Address
        :param tl: transfer length
        :param rdprotect=0:
        :param dpo=0:
        :param fua=0:
        :param rarc=0:
        :param group=0:
        """
        if blocksize == 0:
            raise SCSICommand.MissingBlocksizeException

        SCSICommand.__init__(self, opcode, 0, blocksize * tl)

        self.cdb = self.build_cdb(
            opcode=self.opcode.value,
            lba=lba,
            tl=tl,
            rdprotect=rdprotect,
            dpo=dpo,
            fua=fua,
            rarc=rarc,
            group=group,
        )

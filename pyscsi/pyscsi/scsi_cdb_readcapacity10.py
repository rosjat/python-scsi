# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg<ronniesahlberg@gmail.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pyscsi.pyscsi.scsi_command import SCSICommand

if TYPE_CHECKING:
    from pyscsi.pyscsi.scsi_opcode import OpCode
from pyscsi.utils.converter import CheckDict, decode_bits, encode_dict

#
# SCSI ReadCapacity10 command and definitions
#


class ReadCapacity10(SCSICommand):
    """
    A class to hold information from a ReadCapacity(10) command to a scsi device
    """

    _cdb_bits: CheckDict = {
        "opcode": [0xFF, 0],
    }

    _datain_bits: CheckDict = {
        "returned_lba": [0xFFFFFFFF, 0],
        "block_length": [0xFFFFFFFF, 4],
    }

    def __init__(self, opcode: "OpCode", alloclen: int = 8) -> None:
        """
        initialize a new instance

        :param opcode: a OpCode instance
        :param alloclen: the max number of bytes allocated for the data_in buffer
        """
        SCSICommand.__init__(self, opcode, 0, alloclen)

        self.cdb = self.build_cdb(opcode=self.opcode.value)

    @classmethod
    def unmarshall_datain(cls, data: bytearray) -> Dict[str, Any]:
        """
        Unmarshall the ReadCapacity10 datain.

        :param data: a byte array
        :return result: a dict
        """
        result: Dict[str, Any] = {}
        decode_bits(data, cls._datain_bits, result)
        return result

    @classmethod
    def marshall_datain(cls, data: Dict[str, Any]) -> bytearray:
        """
        Marshall the ReadCapacity10 datain.

        :param data: a dict
        :return result: a byte array
        """
        result = bytearray(8)
        encode_dict(data, cls._datain_bits, result)
        return result

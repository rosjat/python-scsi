# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg<ronniesahlberg@gmail.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pyscsi.pyscsi.scsi_command import SCSICommand
from pyscsi.utils.typedefs import CheckDict

if TYPE_CHECKING:
    from pyscsi.pyscsi.scsi_opcode import OpCode

from pyscsi.utils.converter import (
    decode_bits,
    encode_dict,
    scsi_ba_to_int,
    scsi_int_to_ba,
)

#
# SCSI GetLBAStatus command and definitions
#


class GetLBAStatus(SCSICommand):
    """
    A class to hold information from a GetLBAStatus command to a scsi device
    """

    _cdb_bits: CheckDict = {
        "opcode": [0xFF, 0],
        "service_action": [0x1F, 1],
        "lba": [0xFFFFFFFFFFFFFFFF, 2],
        "alloc_len": [0xFFFFFFFF, 10],
    }
    _datain_bits: CheckDict = {
        "lba": [0xFFFFFFFFFFFFFFFF, 0],
        "num_blocks": [0xFFFFFFFF, 8],
        "p_status": [0x0F, 12],
    }

    def __init__(self, opcode: "OpCode", lba: int, alloclen: int = 16384) -> None:
        """
        initialize a new instance

        :param opcode: a OpCode instance
        :param lba: a local block address
        :param alloclen: the max number of bytes allocated for the data_in buffer
        """
        SCSICommand.__init__(self, opcode, 0, alloclen)
        self.cdb = self.build_cdb(
            opcode=self.opcode.value,
            service_action=self.opcode.serviceaction.GET_LBA_STATUS,
            lba=lba,
            alloc_len=alloclen,
        )

    @classmethod
    def unmarshall_datain(cls, data: bytearray) -> Dict[str, Any]:
        """
        Unmarshall the GetLBAStatus datain.

        :param data: a byte array
        :return result: a dict
        """
        result: Dict[str, Any] = {}
        _data = data[8 : scsi_ba_to_int(data[:4]) + 4]
        _lbas: List[Any] = []
        while len(_data):
            _r: Dict[str, Any] = {}
            decode_bits(_data[:16], cls._datain_bits, _r)

            _lbas.append(_r)
            _data = _data[16:]

        result.update({"lbas": _lbas})
        return result

    @classmethod
    def marshall_datain(cls, data: Dict[str, Any]) -> bytearray:
        """
        Marshall the GetLBAStatus datain.

        :param data: a dict
        :return result: a byte array
        """
        result = bytearray(8)
        if "lbas" not in data:
            result[:4] = scsi_int_to_ba(len(result) - 4, 4)
            return result

        for l in data["lbas"]:
            _r = bytearray(16)
            encode_dict(l, cls._datain_bits, _r)

            result += _r

        result[:4] = scsi_int_to_ba(len(result) - 4, 4)
        return result

# coding: utf-8

# Copyright (C) 2016 by Markus Rosjat<markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pyscsi.pyscsi.scsi_command import SCSICommand
from pyscsi.utils.typedefs import CheckDict

if TYPE_CHECKING:
    from pyscsi.pyscsi.scsi_opcode import OpCode

from pyscsi.pyscsi.scsi_transport_id import (
    marshall_transport_id,
    unmarshall_transport_id,
)
from pyscsi.utils.converter import (
    decode_bits,
    encode_dict,
    scsi_ba_to_int,
    scsi_int_to_ba,
)

#
# SCSI ReportPriority command and definitions
#


class ReportPriority(SCSICommand[Dict[str, Any]]):
    """
    A class to hold information from a ReportPriority command to a scsi device
    """

    _cdb_bits: CheckDict = {
        "opcode": [0xFF, 0],
        "service_action": [0x1F, 1],
        "priority_reported": [0xC0, 2],
        "alloc_len": [0xFFFFFFFF, 6],
    }

    _data_bits: CheckDict = {
        "current_priority": [0x0F, 0],
        "rtpi": [0xFFFF, 2],
        "adlen": [0xFFFF, 6],
    }

    def __init__(
        self, opcode: "OpCode", priority: int = 0, alloclen: int = 16384
    ) -> None:
        """
        initialize a new instance

        :param opcode: a OpCode instance
        :param priority: specifies information to be returned in data_in buffer
        :param alloclen: the max number of bytes allocated for the data_in buffer
        """
        SCSICommand.__init__(self, opcode, 0, alloclen)

        self.cdb = self.build_cdb(
            opcode=self.opcode.value,
            service_action=self.opcode.serviceaction.REPORT_PRIORITY,
            priority_reported=priority,
            alloc_len=alloclen,
        )

    @classmethod
    def unmarshall_datain(cls, data: bytearray) -> Dict[str, Any]:
        """
        Unmarshall the ReportPriority datain.

        :param data: a byte array
        :return result: a dic
        """
        result: Dict[str, Any] = {}
        #  get the data after the ppd_len
        _data = data[4 : 4 + scsi_ba_to_int(data[:4])]
        _descriptors: List[Any] = []
        while len(_data):
            _r: Dict[str, Any] = {}
            # ADDITIONAL DESCRIPTOR LENGTH is a two-byte field at bytes 6-7 and
            # gives the size of the TransportID that follows it.
            _adlen = scsi_ba_to_int(_data[6:8])
            decode_bits(_data[: 8 + _adlen], cls._data_bits, _r)
            _r["transport_id"] = unmarshall_transport_id(_data[8 : 8 + _adlen])
            _descriptors.append(_r)
            _data = _data[8 + _adlen :]
        result.update(
            {
                "priority_descriptors": _descriptors,
            }
        )
        return result

    @classmethod
    def marshall_datain(cls, data: Dict[str, Any]) -> bytearray:
        """
        Marshall the ReportPriority datain.

        :param data: a dict
        :return result: a byte array
        """
        result = bytearray(4)
        if "priority_descriptors" not in data:
            result[:4] = scsi_int_to_ba(len(result) - 4, 4)
            return result

        for l in data["priority_descriptors"]:
            _tid = marshall_transport_id(l["transport_id"])
            _r = bytearray(8 + len(_tid))
            encode_dict(l, cls._data_bits, _r)
            # ADDITIONAL DESCRIPTOR LENGTH is the size of the TransportID, so
            # it follows from the marshalled bytes rather than the input dict.
            _r[6:8] = scsi_int_to_ba(len(_tid), 2)
            _r[8:] = _tid
            result += _r

        result[:4] = scsi_int_to_ba(len(result) - 4, 4)
        return result

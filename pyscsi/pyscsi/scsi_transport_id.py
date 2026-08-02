# coding: utf-8

# Copyright (C) 2015 by Markus Rosjat<markus.rosjat@gmail.com>
# Copyright (C) 2023 by Brian Meagher<brian.meagher@ixsystems.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Any, Dict

from pyscsi.pyscsi.scsi_enum_persistentreserve import PROTOCOL_ID
from pyscsi.utils.converter import (
    decode_bits,
    encode_dict,
    scsi_ba_to_int,
    scsi_int_to_ba,
)

__all__ = ["marshall_transport_id", "unmarshall_transport_id"]

# TransportID, SPC-5 7.6.4. More than one command carries one, so it lives here
# rather than inside whichever command needed it first.
_transport_id_bits = {
    "tpid_format": [0xC0, 0],
    "protocol_id": [0x0F, 0],
}


def _pad4_len(s: str) -> int:
    """
    Calculate the number of bytes necessary to hold the specified string incl a null
    terminator, padded to a multiple of 4 bytes
    """
    _l = len(s) + 1
    _rem = _l % 4
    if _rem:
        _l += 4 - _rem
    return _l


def unmarshall_transport_id(data: bytearray) -> Dict[str, Any]:
    """
    unmarshall TransportID data

    :param data: a byte array with TransportID data
    :return: a dict
    """
    _r: Dict[str, Any] = {}
    decode_bits(data, _transport_id_bits, _r)
    # Now decode the SCSI transport protocol specific data (SPC-5 7.6.4)
    # There may be scope for improvement here for protocol experts
    # equipped with the relevant standards, in the meantime return the
    # data
    _protocol_id = _r["protocol_id"]
    if _protocol_id == PROTOCOL_ID.FIBRE_CHANNEL:
        _r["n_port_name"] = data[8:16]
    elif _protocol_id == PROTOCOL_ID.IEEE_1394:
        _r["eui64_name"] = data[8:16]
    elif _protocol_id == PROTOCOL_ID.RDMA:
        _r["initiator_port_identifier"] = data[8:24]
    elif _protocol_id == PROTOCOL_ID.ISCSI:
        _al = scsi_ba_to_int(data[2:4])
        if _r["tpid_format"] == 0:
            # ISCSI NAME is null-terminated, null-padded
            _r["iscsi_name"] = data[4 : _al + 4].decode("utf-8").rstrip("\0")
        elif _r["tpid_format"] == 1:
            # ISCSI NAME is not null-terminated, but ISCSI INITIATOR SESSION ID is.
            _full_str = data[4 : _al + 4].decode("utf-8").rstrip("\0")
            (_r["iscsi_name"], _r["iscsi_initiator_session_id"]) = _full_str.split(
                ",i,0x"
            )
        else:
            raise ValueError("Invalid TPID FORMAT: %s" % _r["tpid_format"])
    elif _protocol_id == PROTOCOL_ID.SAS:
        _r["sas_address"] = data[4:12]
    elif _protocol_id == PROTOCOL_ID.SOP:
        _r["routing_id"] = data[4:12]
    else:
        raise ValueError("Invalid PROTOCOL ID: %s" % _protocol_id)
    return _r


def marshall_transport_id(data: Dict[str, Any]) -> bytearray:
    """
    marshall TransportID data

    :param data: a dict with TransportID data
    :return result: a byte array
    """
    _protocol_id = data["protocol_id"]
    if _protocol_id != PROTOCOL_ID.ISCSI:
        result = bytearray(24)
        encode_dict(data, _transport_id_bits, result)

    if _protocol_id == PROTOCOL_ID.FIBRE_CHANNEL:
        result[8:16] = data["n_port_name"][:8]
    elif _protocol_id == PROTOCOL_ID.IEEE_1394:
        result[8:16] = data["eui64_name"][:8]
    elif _protocol_id == PROTOCOL_ID.RDMA:
        result[8:24] = data["initiator_port_identifier"][:16]
    elif _protocol_id == PROTOCOL_ID.ISCSI:
        if data.get("tpid_format") and not data.get("iscsi_initiator_session_id"):
            raise ValueError("Must specify iscsi_initiator_session_id")
        if data.get("iscsi_initiator_session_id"):
            if not data.get("tpid_format"):
                raise ValueError("Must specify tpid_format=1")
            _str = f"{data['iscsi_name']},i,0x{data['iscsi_initiator_session_id']}"
        else:
            _str = data["iscsi_name"]
        result = bytearray(4 + _pad4_len(_str))
        encode_dict(data, _transport_id_bits, result)
        result[2:4] = scsi_int_to_ba(len(result) - 4, 2)
        result[4 : len(_str) + 4] = _str.encode("utf-8")
    elif _protocol_id == PROTOCOL_ID.SAS:
        result[4:12] = data["sas_address"][:8]
    elif _protocol_id == PROTOCOL_ID.SOP:
        result[4:12] = data["routing_id"][:8]

    return result

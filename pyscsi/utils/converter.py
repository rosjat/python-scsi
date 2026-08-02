# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg<ronniesahlberg@gmail.com>
# Copyright (C) 2015 by Markus Rosjat<markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterator,
    Mapping,
    Sequence,
    Tuple,
    Union,
    cast,
)

if TYPE_CHECKING:
    from pyscsi.pyscsi.scsi_opcode import OpCode, OpcodeTable

# A field layout entry is one of two shapes:
#
#   [bitmask, offset]                  the legacy form
#   ('b' | 'w' | 'dw', offset, length) a byte/word/dword blob
#
# Neither len(val) == 2 nor isinstance(val, tuple) discriminates them: the
# tables mix lists and tuples for both forms. The element type therefore stays
# Any and the two readers below cast at the point of use; validate_check_dict
# enforces the contract at runtime across every table instead.
FieldNotation = Sequence[Any]
CheckDict = Mapping[str, FieldNotation]

DecodedValue = Union[int, bytearray]


def scsi_int_to_ba(to_convert: int = 0, array_size: int = 4) -> bytearray:
    """
    This function converts a  integer of (8 *array_size)-bit to a bytearray(array_size) in
    BigEndian byte order. Here we use the 32-bit as default.

    example:

        >>scsi_to_ba(34,4)
        bytearray(b'\x00\x00\x00"')

        so we take a 32-bit integer and get a byte array(4)

    :param to_convert: a integer
    :param array_size: a integer defining the size of the byte array
    :return: a byte array
    """
    return bytearray((to_convert >> i * 8) & 0xFF for i in reversed(range(array_size)))


def scsi_ba_to_int(ba: Sequence[int]) -> int:
    """
    This function converts a bytearray  in BigEndian byte order
    to an integer.

    :param ba: a bytearray
    :return: an integer
    """
    return sum(ba[i] << ((len(ba) - 1 - i) * 8) for i in range(len(ba)))


def decode_bits(
    data: bytearray,
    check_dict: CheckDict,
    result_dict: Dict[str, Any],
) -> None:
    """
    helper method to perform some simple bit operations

    the list in the value of each key:value pair contains 2 values
    - the bit mask
    - the offset byte in the datain byte array

    for now we assume he have to right shift only

    :param data: a buffer containing the bits to decode
    :param check_dict: a dict mapping field-names to notation tuples.
    :param result_dict: a dict mapping field-names to notation tuples.
    """
    for key in check_dict.keys():
        # Notation format:
        #
        # If the length is 2 we have the legacy notation [bitmask, offset]
        # Example: 'sync': [0x10, 7],
        #
        # >2-tuples is the new style of notation.
        # These tuples always consist of at least three elements, where the
        # first element is a string that describes the type of value.
        #
        # 'b': Byte array blobs
        # ----------------
        # ('b', offset, length)
        # Example: 't10_vendor_identification': ('b', 8, 8),
        #

        val = check_dict[key]
        # Deliberately left unassigned when no branch matches, which is what
        # the callers have always seen: the previous iteration's value is
        # written under this key, and an unmatched first entry raises
        # UnboundLocalError. Annotating must not change that.
        value: DecodedValue
        if len(val) == 2:
            bitmask, byte_pos = cast(Tuple[int, int], val)
            _num = 1
            _bm = bitmask
            while _bm > 0xFF:
                _bm >>= 8
                _num += 1
            value = scsi_ba_to_int(data[byte_pos : byte_pos + _num])
            while not bitmask & 0x01:
                bitmask >>= 1
                value >>= 1
            value &= bitmask
        elif val[0] == "b":
            _, offset, length = cast(Tuple[str, int, int], val)
            value = data[offset : offset + length]
        elif val[0] == "w":
            _, offset, length = cast(Tuple[str, int, int], val)
            value = data[offset : offset + length * 2]
        elif val[0] == "dw":
            _, offset, length = cast(Tuple[str, int, int], val)
            value = data[offset : offset + length * 4]
        result_dict.update({key: value})


def encode_dict(
    data_dict: Mapping[str, Any],
    check_dict: CheckDict,
    result: bytearray,
) -> None:
    """
    helper method to perform some simple bit operations

    the list in the value of each key:value pair contains 2 values
    - the bit mask
    - the offset byte in the datain byte array

    for now we assume he have to right shift only

    Bitmask fields are written with ^=, so `result` must be zeroed and must not
    be encoded into twice: a second pass toggles bits back off.

    :param data_dict:  a dict mapping field-names to notation tuples.
    :param check_dict: a dict mapping field-names to notation tuples.
    :param result: a buffer containing the bits encoded
    """
    for key in data_dict.keys():
        if key not in check_dict:
            continue
        value = data_dict[key]

        val = check_dict[key]
        if len(val) == 2:
            bitmask, bytepos = cast(Tuple[int, int], val)

            _num = 1
            _bm = bitmask
            while _bm > 0xFF:
                _bm >>= 8
                _num += 1

            _bm = bitmask
            while not _bm & 0x01:
                _bm >>= 1
                value <<= 1

            v = scsi_int_to_ba(value, _num)
            for i in range(len(v)):
                result[bytepos + i] ^= v[i]
        elif val[0] == "b":
            _, offset, length = cast(Tuple[str, int, int], val)
            result[offset : offset + length] = value
        elif val[0] == "w":
            _, offset, length = cast(Tuple[str, int, int], val)
            result[offset : offset + length * 2] = value
        elif val[0] == "dw":
            _, offset, length = cast(Tuple[str, int, int], val)
            result[offset : offset + length * 4] = value


def print_data(data_dict: Mapping[str, Any]) -> None:
    """
    A small method to print out data we generate in this package.

    It's not really a converter but in a way we convert a dict of
    key - value pairs into strings ...

    :param data_dict: a dictionary
    :return: a few strings
    """
    for k, v in data_dict.items():
        if isinstance(v, dict):
            print(k)
            print_data(v)
        else:
            if isinstance(v, str):
                print("%s -> %s" % (k, v))
            elif isinstance(v, float):
                print("%s -> %.02d" % (k, v))
            else:
                print("%s -> 0x%02X" % (k, v))


def get_opcode(table: "OpcodeTable", part: str) -> Iterator["OpCode"]:
    """
    A generator that yields OpCode objects from a given opcode table.

    Used for opcodes multiplexed over service actions, which live under
    synthetic keys such as SBC_OPCODE_9E and are matched on the last two
    characters of the key.

    :param table: the OpcodeTable to search
    :param part: a string to look up in the table keys
    :return: an OpCode object
    """
    for name, opcode in table.items():
        if name[len(name) - 2 :] == part:
            yield opcode

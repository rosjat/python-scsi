# coding: utf-8

# SPDX-FileCopyrightText: 2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Type aliases shared across the package."""

from typing import TYPE_CHECKING, Any, Dict, Mapping, Protocol, Sequence, Union

if TYPE_CHECKING:
    from pyscsi.pyscsi.scsi_command import SCSICommand
    from pyscsi.pyscsi.scsi_opcode import OpcodeTable

__all__ = [
    "CheckDict",
    "CodeTable",
    "DecodedValue",
    "Device",
    "FieldNotation",
]

# A field layout entry is one of two shapes:
#
#   [bitmask, offset]                  the legacy form
#   ('b' | 'w' | 'dw', offset, length) a byte/word/dword blob
#
# A Union of the two cannot be checked: the tables write both forms as literals
# in one dict, so mypy joins them to Sequence[str | int], and isinstance on
# val[0] narrows the element rather than the container. The element type stays
# Any and the readers in converter cast at the point of use; the shape is
# enforced at runtime by validate_check_dict, which test_check_dict_shapes runs
# over every table in the package.
FieldNotation = Sequence[Any]
CheckDict = Mapping[str, FieldNotation]

DecodedValue = Union[int, bytearray]

# EXTENDED COPY name/description/size tables keyed by code. The mixed value
# types would otherwise join to object, which is not indexable or sizeable.
CodeTable = Dict[int, Dict[str, Any]]


class Device(Protocol):
    """What SCSI requires of a transport.

    SCSIDevice and ISCSIDevice are duck-typed siblings with no common base, and
    tests/mock_device.py stands in for both. Structural typing is what lets all
    three satisfy this without inheriting.

    open() is deliberately absent. SCSIDevice.open() takes no argument and
    ISCSIDevice.open(device) requires one, so no caller can treat them alike --
    and none does: open() is only ever called by a device on itself.
    """

    opcodes: "OpcodeTable"
    devicetype: int

    def execute(self, cmd: "SCSICommand[Any]", en_raw_sense: bool = False) -> None: ...

    def close(self) -> None: ...

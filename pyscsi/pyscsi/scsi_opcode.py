# coding: utf-8

# Copyright (C) 2015 by Markus Rosjat<markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Mapping, Optional

from pyscsi.utils.table import Table, ValueTable

__all__ = [
    "OpCode",
    "OpcodeTable",
]


class OpCode:
    """
    A class to hold information about a scsi operation code
    """

    __slots__ = ("name", "value", "serviceaction")

    def __init__(
        self,
        name: str,
        code: int,
        serviceaction: Optional[Mapping[str, int]] = None,
    ) -> None:
        """
        initialize a new instance

        :param name: a string representing the name of the operation code
        :param code: a hexadecimal value representing the value associated with the operation code
        :param serviceaction: a mapping of service actions supported by the command
                              associated with the operation code
        """
        self.name = name
        self.value = code
        self.serviceaction = ValueTable(dict(serviceaction or {}))

    def __repr__(self) -> str:
        return f"{self.name} - {self.value:x}"

    __str__ = __repr__


class OpcodeTable(Table[OpCode]):
    """``name -> OpCode``, one per device type (spc, sbc, ssc, smc, mmc)."""

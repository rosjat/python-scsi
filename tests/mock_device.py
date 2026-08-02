# coding: utf-8

# Copyright (C) 2015 by Markus Rosjat<markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Any, Optional

from pyscsi.pyscsi.scsi import SCSI
from pyscsi.pyscsi.scsi_command import SCSICommand
from pyscsi.pyscsi.scsi_opcode import OpcodeTable
from pyscsi.utils.typedefs import Device


class MockSCSI(SCSI):
    def __init__(self, dev: Device) -> None:
        # Deliberately does not call SCSI.__init__: that issues an INQUIRY to
        # pick an opcode table, and the tests supply one directly.
        self.device = dev


class MockDevice:
    _opcodes: Optional[OpcodeTable] = None

    # Never set by MockSCSI, which bypasses SCSI.__init__ and so never runs
    # __init_opcode. Declared so the mock still satisfies utils.typedefs.Device.
    devicetype: int = 0

    def __init__(self, opcodes: OpcodeTable) -> None:
        self.opcodes = opcodes

    @property
    def opcodes(self) -> OpcodeTable:
        assert self._opcodes is not None
        return self._opcodes

    @opcodes.setter
    def opcodes(self, value: OpcodeTable) -> None:
        self._opcodes = value

    def execute(self, cmd: SCSICommand[Any], en_raw_sense: bool = False) -> None:
        pass

    def open(self) -> None:
        pass

    def close(self) -> None:
        pass

# coding: utf-8

# Copyright (C) 2015 by Markus Rosjat<markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from pyscsi.pyscsi.scsi import SCSI


class MockSCSI(SCSI):
    def __init__(self, dev):
        self.device = dev


class MockDevice:
    _opcodes = None

    # Never set by MockSCSI, which bypasses SCSI.__init__ and so never runs
    # __init_opcode. Declared so the mock still satisfies utils.typedefs.Device.
    devicetype: int = 0

    def __init__(self, opcodes):
        self.opcodes = opcodes

    @property
    def opcodes(self):
        return self._opcodes

    @opcodes.setter
    def opcodes(self, value):
        self._opcodes = value

    def execute(self, cmd, en_raw_sense: bool = False):
        pass

    def open(self):
        pass

    def close(self):
        pass

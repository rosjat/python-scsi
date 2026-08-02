# coding: utf-8

# Copyright (C) 2015 by Markus Rosjat<markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import TYPE_CHECKING, Any, Dict

from pyscsi.pyscsi.scsi_command import SCSICommand

if TYPE_CHECKING:
    from pyscsi.pyscsi.scsi_opcode import OpCode

#
# SCSI InitializeElementStatusWithRange command and definitions
#


class InitializeElementStatusWithRange(SCSICommand[Dict[str, Any]]):
    """
    A class to hold information from a InitializeElementStatusWithRange command
    to a scsi device
    """

    _cdb_bits = {
        "opcode": [0xFF, 0],
        "fast": [0x02, 1],
        "range": [0x01, 1],
        "starting_element_address": [0xFFFF, 2],
        "number_of_elements": [0xFFFF, 6],
    }

    def __init__(
        self, opcode: "OpCode", xfer: int, elements: int, rng: int = 0, fast: int = 0
    ) -> None:
        """
        initialize a new instance

        :param opcode: a OpCode instance
        :param xfer: starting element address
        :param elements: number of elements
        :param rng: range  indicates if all elements should be checked, if set to 1 xfer
                    and elements are ignored
        :param fast: fast , if set to 1 scan for media presence only. If set to 0 scan
                     elements for all relevant status.
        """
        SCSICommand.__init__(self, opcode, 0, 0)

        self.cdb = self.build_cdb(
            opcode=self.opcode.value,
            starting_element_address=xfer,
            number_of_elements=elements,
            range=rng,
            fast=fast,
        )

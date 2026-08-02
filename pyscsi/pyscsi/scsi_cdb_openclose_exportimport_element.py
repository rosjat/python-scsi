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
# SCSI OpenCloseImportExportElement command and definitions
#


class OpenCloseImportExportElement(SCSICommand[Dict[str, Any]]):
    """
    A class to hold information from a OpenCloseImportExportElement
    command to a scsi device
    """

    _cdb_bits = {
        "opcode": [0xFF, 0],
        "element_address": [0xFFFF, 2],
        "action_code": [0x1F, 4],
    }

    def __init__(self, opcode: "OpCode", xfer: int, acode: int, **kwargs: Any) -> None:
        """
        initialize a new instance

        :param opcode: a OpCode instance
        :param xfer: element address
        :param acode: action code
        """
        SCSICommand.__init__(self, opcode, 0, 0)

        self.cdb = self.build_cdb(
            opcode=self.opcode.value,
            element_address=xfer,
            action_code=acode,
        )

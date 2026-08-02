# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg<ronniesahlberg@gmail.com>
# Copyright (C) 2015 by Markus Rosjat<markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

import os
from types import TracebackType
from typing import IO, Any, ClassVar, Optional, Type, cast

import pyscsi.pyscsi.scsi_enum_command as scsi_enum_command
from pyscsi.pyscsi.scsi_command import SCSICommand
from pyscsi.pyscsi.scsi_exception import SCSIDeviceCommandExceptionMeta as ExMETA
from pyscsi.pyscsi.scsi_opcode import OpcodeTable

try:
    import sgio

    _has_sgio = True
except ImportError as e:
    _has_sgio = False


def get_inode(file):
    #  type: (str) -> int
    return os.stat(file).st_ino


class SCSIDevice(metaclass=ExMETA):
    """
    The scsi device class

    By default it gets the SPC opcodes assigned so it's always possible to issue
    a inquiry command to the device. This is important since the the Command will
    figure out the opcode from the SCSIDevice first to use it for building the cdb.
    This means after the that it's possible to use the proper OpCodes for the device.
    A basic workflow for using a device would be:
        - try to open the device passed by the device arg
        - create a  Inquiry instance, with the default opcodes of the device
        - execute the inquiry with the device
        - unmarshall the datain from the inquiry command to figure out the device type
        - assign the proper Opcode for the device type (it would also work just to use the
          opcodes without assigning them to the device since the command builds the cdb
          and the device just executes)

    Note: The workflow above is already implemented in the SCSI class
    """

    # ExMETA injects all ten, both families, so all ten are declared. Omitting
    # any leaves a working attribute that mypy rejects and types as Any;
    # test_exception_injection pins the two sets together.
    ACAActive: ClassVar[Type[Exception]]
    BusyStatus: ClassVar[Type[Exception]]
    CheckCondition: ClassVar[Type[Exception]]
    CommandNotImplemented: ClassVar[Type[Exception]]
    ConditionsMet: ClassVar[Type[Exception]]
    MissingBlocksizeException: ClassVar[Type[Exception]]
    OpcodeException: ClassVar[Type[Exception]]
    ReservationConflict: ClassVar[Type[Exception]]
    TaskAborted: ClassVar[Type[Exception]]
    TaskSetFull: ClassVar[Type[Exception]]

    def __init__(
        self,
        device: str,
        readwrite: bool = False,
        detect_replugged: bool = True,
        buffering: int = -1,
    ) -> None:
        """
        initialize a  new instance of a SCSIDevice
        :param device: the file descriptor
        :param readwrite: access type
        :param detect_replugged: detects device unplugged and plugged events and ensure executions will not fail
        silently due to replugged events
        :param buffering: Set the amount of buffering. For details, refer to the documentation of the open() built-in
        """
        self._opcodes: OpcodeTable = scsi_enum_command.spc
        self._file_name = device
        self._read_write = readwrite
        self._file: Optional[IO[bytes]] = None
        self._ino: Optional[int] = None
        self._devicetype: int
        self._detect_replugged = detect_replugged
        self._buffering = buffering

        if _has_sgio and device[:5] == "/dev/":
            self.open()
        else:
            raise NotImplementedError("No backend implemented for %s" % device)

    def __enter__(self) -> "SCSIDevice":
        """

        :return:
        """
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
        self.close()

    def __repr__(self) -> str:
        """

        :return:
        """
        return self.__class__.__name__

    def _is_replugged(self) -> bool:
        ino = get_inode(self._file_name)
        return ino != self._ino

    def open(self) -> None:
        """

        :param dev:
        :param read_write:
        :return:
        """
        self._file = open(
            self._file_name,
            "w+b" if self._read_write else "rb",
            buffering=self._buffering,
        )
        self._ino = get_inode(self._file_name)

    def close(self) -> None:
        cast(IO[bytes], self._file).close()

    def execute(self, cmd: SCSICommand[Any], en_raw_sense: bool = False) -> None:
        """
        execute a scsi command

        :param cmd: a SCSICommand
        """
        if self._detect_replugged and self._is_replugged():
            try:
                self.close()
            finally:
                self.open()

        try:
            # TODO: If exist the corner case that sense cannot be raised by error.sense?
            # will not set return_sense_data=True until i test most of the ata command set.
            sgio.execute(self._file, cmd.cdb, cmd.dataout, cmd.datain)
        except sgio.CheckConditionError as error:
            self.CheckCondition(error.sense)
            # For ata-passthrough, mostly the scsi command return no real error, here
            # save the raw sense data to command.raw_sense_data for upper level use.
            # If you execute the other scsi commands with en_raw_sense=True, this will
            # be a coppy of error.sense
            if en_raw_sense:
                cmd.raw_sense_data = error.sense

    @property
    def opcodes(self) -> OpcodeTable:
        return self._opcodes

    @opcodes.setter
    def opcodes(self, value: OpcodeTable) -> None:
        self._opcodes = value

    @property
    def devicetype(self) -> int:
        return self._devicetype

    @devicetype.setter
    def devicetype(self, value: int) -> None:
        self._devicetype = value

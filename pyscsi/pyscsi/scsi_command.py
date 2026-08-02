# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg<ronniesahlberg@gmail.com>
# Copyright (C) 2016 by Markus Rosjat<markus.rosjat@gmail.com>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import (
    TYPE_CHECKING,
    Any,
    ClassVar,
    Dict,
    Generic,
    Optional,
    Type,
    TypeVar,
    cast,
)

from pyscsi.pyscsi.scsi_exception import SCSIDeviceCommandExceptionMeta as ExMETA
from pyscsi.utils.converter import decode_bits, encode_dict
from pyscsi.utils.typedefs import CheckDict

if TYPE_CHECKING:
    from pyscsi.pyscsi.scsi_opcode import OpCode


# The shape of `result` is per command: almost all key it by field name, but
# READ CD returns one entry per sector and keys by LBA. A single declared type
# cannot describe both -- dict is invariant in its key, so no Union works in
# either direction -- so the base is generic and each command binds its own.
ResultT = TypeVar("ResultT")


class SCSICommand(Generic[ResultT], metaclass=ExMETA):
    """
    The base class for a derived scsi command class
    """

    _cdb_bits: CheckDict = {}
    _cdb: Optional[bytearray] = None
    _sense: Optional[bytearray] = None
    _raw_sense_data: Optional[bytearray] = None
    _datain: Optional[bytearray] = None
    _dataout: Optional[bytearray] = None
    _result: Optional[ResultT] = None
    _page_code: Optional[int] = None
    _opcode: Optional["OpCode"] = None

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
        opcode: "OpCode",
        dataout_alloclen: int,
        datain_alloclen: int,
    ) -> None:
        """
        initialize a new instance

        :param opcode: a OpCode instance
        :param dataout_alloclen: integer representing the size of the data_out buffer
        :param datain_alloclen: integer representing the size of the data_in buffer
        """
        self._cdb = SCSICommand.init_cdb(opcode)
        self.dataout = bytearray(dataout_alloclen)
        self.datain = bytearray(datain_alloclen)
        # Every command binds ResultT to a dict type, so an empty one is the
        # right initial value; the base cannot prove that for an arbitrary bind.
        self.result = cast(ResultT, {})
        self.page_code = None
        self.opcode = opcode

    def __repr__(self) -> str:
        return self.__class__.__name__

    @staticmethod
    def init_cdb(opcode: "OpCode") -> bytearray:
        """
        init a byte array representing a command descriptor block with fixed length
        depending on the Opcode

        :param opcode: a OpCode object
        :return: a byte array
        """
        return bytearray(SCSICommand.cdb_length(opcode.value))

    @staticmethod
    def cdb_length(opcode_value: int) -> int:
        """
        length in bytes of the command descriptor block for an operation code

        The length follows the operation code's group code, which is the top
        three bits of the opcode:

          group 0   0x00-0x1F    6 bytes
          group 1   0x20-0x3F   10 bytes
          group 2   0x40-0x5F   10 bytes
          group 3   0x60-0x7F   not a fixed length -- 0x7E is the extended CDB
                                and 0x7F the variable length CDB, whose size
                                comes from the additional length field
          group 4   0x80-0x9F   16 bytes
          group 5   0xA0-0xBF   12 bytes
          group 6   0xC0-0xDF   vendor specific
          group 7   0xE0-0xFF   vendor specific

        :param opcode_value: the operation code as an integer
        :return: the CDB length in bytes
        """
        if 0x00 <= opcode_value <= 0x1F:
            return 6
        if 0x20 <= opcode_value <= 0x5F:
            return 10
        if 0x60 <= opcode_value <= 0x7F:
            # Group 3 has no fixed length: its size comes from the additional
            # length field in the CDB itself, which is not visible here. A
            # command built on 0x7E or 0x7F needs its own sizing.
            raise SCSICommand.OpcodeException(
                f"opcode 0x{opcode_value:02X} is a group 3 variable length CDB,"
                " whose size comes from the additional length field rather than"
                " the opcode"
            )
        if 0x80 <= opcode_value <= 0x9F:
            return 16
        if 0xA0 <= opcode_value <= 0xBF:
            return 12
        # Groups 6 and 7 are vendor specific, so their length is not defined by
        # the standard.
        raise SCSICommand.OpcodeException(
            f"opcode 0x{opcode_value:02X} is vendor specific and has no"
            " CDB length defined by the standard"
        )

    @property
    def result(self) -> ResultT:
        """
        getter method of the result property

        :return: a dictionary
        """
        return cast(ResultT, self._result)

    @result.setter
    def result(self, value: ResultT) -> None:
        """
        setter method of the result property

        :param value: a dictionary
        """
        self._result = value

    @property
    def cdb(self) -> bytearray:
        """
        getter method of the cdb property

        :return: a byte array
        """
        return cast(bytearray, self._cdb)

    @cdb.setter
    def cdb(self, value: bytearray) -> None:
        """
        setter method of the cdb property

        :param value: a byte array
        """
        self._cdb = value

    @property
    def datain(self) -> bytearray:
        """
        getter method of the datain property

        :return: a byte array
        """
        return cast(bytearray, self._datain)

    @datain.setter
    def datain(self, value: bytearray) -> None:
        """
        setter method of the datain property

        :param value: a byte array
        """
        self._datain = value

    @property
    def dataout(self) -> Optional[bytearray]:
        """
        getter method of the dataout property

        :return: a byte array
        """
        return self._dataout

    @dataout.setter
    def dataout(self, value: Optional[bytearray]) -> None:
        """
        setter method of the dataout property

        :param value: a byte array
        """
        self._dataout = value

    @property
    def sense(self) -> Optional[bytearray]:
        """
        getter method of the sense property

        :return: a byte array
        """
        return self._sense

    @sense.setter
    def sense(self, value: Optional[bytearray]) -> None:
        """
        setter method of the sense property

        :param value: a byte array
        """
        self._sense = value

    @property
    def raw_sense_data(self) -> Optional[bytearray]:
        """
        getter method of the raw_sense_data property

        :return: a byte
        """
        return self._raw_sense_data

    @raw_sense_data.setter
    def raw_sense_data(self, value: Optional[bytearray]) -> None:
        """
        setter method of the raw_sense_data property

        :param value: a byte
        """
        self._raw_sense_data = value

    @property
    def pagecode(self) -> Optional[int]:
        """
        getter method of the pagecode property
        """
        return self._page_code

    @pagecode.setter
    def pagecode(self, value: Optional[int]) -> None:
        """
        setter method of the pagecode property

        :param value: a hexadecimal
        """
        self._page_code = value

    @property
    def opcode(self) -> "OpCode":
        """
        getter method of the opcode property
        """
        return cast("OpCode", self._opcode)

    @opcode.setter
    def opcode(self, value: "OpCode") -> None:
        """
        setter method of the opcode property

        :param value: a OpCode object
        """
        self._opcode = value

    def print_cdb(self) -> None:
        """
        simple helper to print out the cdb as hex values
        """

        for b in cast(bytearray, self._cdb):
            print("0x%02X " % b)

    @classmethod
    def marshall_cdb(cls, cdb: Dict[str, Any]) -> bytearray:
        """
        Marshall an SCSICommand cdb

        :param cdb: a dict with key:value pairs representing a code descriptor block
        :return result: a byte array representing a code descriptor block
        """
        result = bytearray(cls.cdb_length(cdb["opcode"]))
        encode_dict(cdb, cls._cdb_bits, result)
        return result

    @classmethod
    def unmarshall_cdb(cls, cdb: bytearray) -> Dict[str, Any]:
        """
        Unmarshall an SCSICommand cdb

        :param cdb: a byte array representing a code descriptor block
        :return result: a dict
        """
        result: Dict[str, Any] = {}
        decode_bits(cdb, cls._cdb_bits, result)
        return result

    def build_cdb(self, **kwargs: Any) -> bytearray:
        """
        Build a SCSICommand CDB

        :param kwargs: keyword argument dict, content depends on SCSICommand subclass
        :return: a byte array representing a code descriptor block
        """
        cdb = {key: kwargs[key] for key in kwargs.keys()}
        return self.marshall_cdb(cdb)

    def unmarshall(self, **kwargs: Any) -> None:
        """
        wrapper method for unmarshall_datain method.

        :param kwargs: keyword argument dict, content depends on SCSICommand subclass
        """
        try:
            unmarshall_datain = getattr(self, "unmarshall_datain")
            if unmarshall_datain:
                self.result = unmarshall_datain(self.datain, **kwargs)
        except AttributeError:
            raise NotImplementedError(
                "%s has no method to unmarshall datain data" % self
            )

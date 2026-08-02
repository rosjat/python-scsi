# coding: utf-8

# Copyright (C) 2015 by Markus Rosjat<markus.rosjat@gmail.com>
# Copyright (C) 2016 by Diego Elio Pettenò <flameeyes@flameeyes.eu>
# SPDX-FileCopyrightText: 2014-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Any, Dict, Tuple, Type

from pyscsi.pyscsi.scsi_sense import SCSICheckCondition


def _command_exceptions() -> Dict[str, Type[Exception]]:
    """A fresh set per host class, which is what makes them distinct."""

    class CommandNotImplemented(Exception):
        pass

    class MissingBlocksizeException(Exception):
        pass

    class OpcodeException(Exception):
        pass

    return {
        "CommandNotImplemented": CommandNotImplemented,
        "MissingBlocksizeException": MissingBlocksizeException,
        "OpcodeException": OpcodeException,
    }


def _device_exceptions() -> Dict[str, Type[Exception]]:
    """A fresh set per host class, which is what makes them distinct."""

    class CheckCondition(SCSICheckCondition):
        pass

    class ConditionsMet(Exception):
        pass

    class BusyStatus(Exception):
        pass

    class ReservationConflict(Exception):
        pass

    class TaskSetFull(Exception):
        pass

    class ACAActive(Exception):
        pass

    class TaskAborted(Exception):
        pass

    return {
        "CheckCondition": CheckCondition,
        "ConditionsMet": ConditionsMet,
        "BusyStatus": BusyStatus,
        "ReservationConflict": ReservationConflict,
        "TaskSetFull": TaskSetFull,
        "ACAActive": ACAActive,
        "TaskAborted": TaskAborted,
    }


class SCSICommandExceptionMeta(type):
    """
    A meta class for class depending SCSICommand exceptions
    """

    def __new__(
        mcs,
        cls: str,
        bases: Tuple[type, ...],
        attributes: Dict[str, Any],
    ) -> type:
        attributes.update(_command_exceptions())
        return type.__new__(mcs, cls, bases, attributes)


class SCSIDeviceExceptionMeta(type):
    """
    A meta class for class depending SCSICommand exceptions
    """

    def __new__(
        mcs,
        cls: str,
        bases: Tuple[type, ...],
        attributes: Dict[str, Any],
    ) -> type:
        attributes.update(_device_exceptions())
        return type.__new__(mcs, cls, bases, attributes)


class SCSIDeviceCommandExceptionMeta(SCSICommandExceptionMeta, SCSIDeviceExceptionMeta):
    def __new__(
        mcs,
        name: str,
        bases: Tuple[type, ...],
        attr: Dict[str, Any],
    ) -> type:
        # Both families, built once. This previously created the class, took its
        # MRO as the new bases and built it a second time. That put plain
        # Generic into bases -- so no host class could be a typing.Generic --
        # and set __class__ twice, which makes zero-arg super() raise TypeError
        # at class creation.
        attr.update(_command_exceptions())
        attr.update(_device_exceptions())
        return type.__new__(mcs, name, bases, attr)

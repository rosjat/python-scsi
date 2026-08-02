# coding: utf-8

# Copyright (C) 2015 by Markus Rosjat<markus.rosjat@gmail.com>
# Copyright (C) 2016 by Diego Elio Pettenò <flameeyes@flameeyes.eu>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from typing import Any, Dict, Tuple, Type

from pyscsi.pyscsi.scsi_sense import SCSICheckCondition


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
        class CommandNotImplemented(Exception):
            pass

        class MissingBlocksizeException(Exception):
            pass

        class OpcodeException(Exception):
            pass

        attributes.update({"CommandNotImplemented": CommandNotImplemented})
        attributes.update({"MissingBlocksizeException": MissingBlocksizeException})
        attributes.update({"OpcodeException": OpcodeException})

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

        attributes.update({"CheckCondition": CheckCondition})
        attributes.update({"ConditionsMet": ConditionsMet})
        attributes.update({"BusyStatus": BusyStatus})
        attributes.update({"ReservationConflict": ReservationConflict})
        attributes.update({"TaskSetFull": TaskSetFull})
        attributes.update({"ACAActive": ACAActive})
        attributes.update({"TaskAborted": TaskAborted})

        return type.__new__(mcs, cls, bases, attributes)


class SCSIDeviceCommandExceptionMeta(SCSICommandExceptionMeta, SCSIDeviceExceptionMeta):
    def __init__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        attr: Dict[str, Any],
    ) -> None:
        SCSICommandExceptionMeta.__init__(cls, name, bases, attr)
        SCSIDeviceExceptionMeta.__init__(cls, name, bases, attr)

    def __new__(
        mcs,
        name: str,
        bases: Tuple[type, ...],
        attr: Dict[str, Any],
    ) -> type:
        t1 = SCSICommandExceptionMeta.__new__(mcs, name, bases, attr)
        name = t1.__name__
        bases = tuple(t1.mro())
        attr = t1.__dict__.copy()
        t2 = SCSIDeviceExceptionMeta.__new__(mcs, name, bases, attr)
        return t2

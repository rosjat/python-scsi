# coding: utf-8

# SPDX-FileCopyrightText: 2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Typed name -> member tables.

These replace the previous ``Enum`` metaclass, which built a class on the fly
so that its members became class attributes. That worked, but a type checker
could never know what those attributes were.

Deliberately not ``enum.Enum``: the SCSI tables contain **duplicate values by
design**. The 0xA3 service-action table alone holds 30 names across 17 distinct
values, and stdlib enum silently aliases members that share a value, keeping
only the first name and discarding the rest.
"""

from typing import Any, Dict, Generic, Iterator, List, Mapping, Optional, Tuple, TypeVar

from pyscsi.utils.exception import NotSupportedArgumentError

__all__ = [
    "BitsTable",
    "Table",
    "ValueTable",
]

T = TypeVar("T")


class Table(Generic[T]):
    """An ordered ``name -> member`` mapping with reverse lookup by value.

    Members are reached as attributes::

        >>> t = ValueTable({"A": 1, "B": 2})
        >>> t.A
        1
        >>> t[2]
        'B'

    Duplicate values are permitted. ``__getitem__`` returns the first matching
    name in insertion order, and a miss yields ``""`` rather than raising --
    callers in ``tools/`` rely on that when printing unknown values.
    """

    __slots__ = ("_members",)

    # Annotated so the slot has a type; otherwise __getattr__ below catches it
    # and every internal use is typed as T.
    _members: Dict[str, T]

    def __init__(
        self,
        members: Optional[Mapping[str, T]] = None,
        /,
        **kwargs: T,
    ) -> None:
        if members is not None:
            if not isinstance(members, Mapping):
                raise NotSupportedArgumentError(
                    "use either as dict or provide keyword arguments"
                )
            if kwargs:
                raise NotSupportedArgumentError(
                    "pass a mapping or keyword arguments, not both"
                )
            data = dict(members)
        elif kwargs:
            data = dict(kwargs)
        else:
            raise NotSupportedArgumentError(
                "use either as dict or provide keyword arguments"
            )
        self._members = data

    def __getattr__(self, name: str) -> T:
        # Guard the private slot: without this, any attribute lookup made
        # before _members is bound (copy, pickle) recurses forever.
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self._members[name]
        except KeyError:
            raise AttributeError(
                f"{type(self).__name__} has no member {name!r}"
            ) from None

    def __getitem__(self, value: object) -> str:
        """Reverse lookup: value -> first name holding it, or ``""``."""
        for key, member in self._members.items():
            if member == value:
                return key
        return ""

    @property
    def keys(self) -> List[str]:
        """Member names, in insertion order."""
        return list(self._members)

    def items(self) -> Iterator[Tuple[str, T]]:
        yield from self._members.items()

    def __contains__(self, name: object) -> bool:
        return name in self._members

    def __iter__(self) -> Iterator[str]:
        return iter(self._members)

    def __len__(self) -> int:
        return len(self._members)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._members!r})"


class ValueTable(Table[int]):
    """``name -> integer code``, e.g. VPD page codes or service actions."""


class BitsTable(Table[Any]):
    """``name -> field-notation dict``, used for the mode page tables."""

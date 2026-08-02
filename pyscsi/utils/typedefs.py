# coding: utf-8

# SPDX-FileCopyrightText: 2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

"""Type aliases shared across the package."""

from typing import Any, Dict, Mapping, Sequence, Tuple, Union

__all__ = [
    "CheckDict",
    "CodeTable",
    "DecodedValue",
    "FieldNotation",
]

# A field layout entry is one of two shapes:
#
#   [bitmask, offset]                  the legacy form
#   ('b' | 'w' | 'dw', offset, length) a byte/word/dword blob
#
# A Union of the two cannot be checked: the tables write both forms as literals
# in one dict, so mypy joins them to Sequence[str | int], and isinstance on
# val[0] narrows the element rather than the container. The element type stays
# Any and the readers in converter cast at the point of use; the shape is
# enforced at runtime by validate_check_dict, which test_check_dict_shapes runs
# over every table in the package.
FieldNotation = Sequence[Any]
CheckDict = Mapping[str, FieldNotation]

DecodedValue = Union[int, bytearray]

# EXTENDED COPY name/description/size tables keyed by code. The mixed value
# types would otherwise join to object, which is not indexable or sizeable.
CodeTable = Dict[int, Dict[str, Any]]

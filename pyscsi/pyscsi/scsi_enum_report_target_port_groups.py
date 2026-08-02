# SPDX-FileCopyrightText: 2022-2026 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

# coding: utf-8


from pyscsi.utils.table import ValueTable

#
# PARAMETER DATA FORMAT TYPE
#
_data_format_type = {
    "LENGTH_ONLY_HEADER_PARAMETER_DATA_FORMAT": 0,
    "EXTENDED_HEADER_PARAMETER_DATA_FORMAT": 1,
}

DATA_FORMAT_TYPE = ValueTable(_data_format_type)

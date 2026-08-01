# coding: utf-8

# Copyright (C) 2014 by Ronnie Sahlberg<ronniesahlberg@gmail.com>
# SPDX-FileCopyrightText: 2014 The python-scsi Authors
#
# SPDX-License-Identifier: LGPL-2.1-or-later

from pyscsi.utils.table import ValueTable

#
# P_TYPE
#
_p_types = {
    "TYPE_1_PROTECTION": 0x00,
    "TYPE_2_PROTECTION": 0x01,
    "TYPE_3_PROTECTION": 0x02,
}

P_TYPE = ValueTable(_p_types)

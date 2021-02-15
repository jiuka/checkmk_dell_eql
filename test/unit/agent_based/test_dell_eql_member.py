#!/usr/bin/env python3
# -*- encoding: utf-8; py-indent-offset: 4 -*-
#
# Checks for Dell EqualLogic Storage System
#
# Copyright (C) 2021  Marius Rieder <marius.rieder@scs.ch>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import pytest  # type: ignore[import]
from cmk.base.plugins.agent_based import dell_eql_member


@pytest.mark.parametrize('bytelist, result', [
    ([0, 0, 0, 0], []),
    ([0, 0, 0, 1], [31]),
    ([8, 4, 2, 1], [4, 13, 22, 31]),
    ([0, 0, 0, 15], [28, 29, 30, 31]),
])
def test_byte_to_index(bytelist, result):
    assert list(dell_eql_member.byte_to_index(bytelist)) == result

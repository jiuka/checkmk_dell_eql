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
from cmk.base.plugins.agent_based.agent_based_api.v1 import (
    Metric,
    Result,
    Service,
    State,
)
from cmk.base.plugins.agent_based import dell_eql_temp


def get_value_store():
    return {}


@pytest.mark.parametrize('string_table, result', [
    (
        [[], []], []
    ),
    (
        [
            [['1234567890', 'MEMBER1']],
            [['1234567890.1', 'Backplane sensor 0', '29', '1', '50', '45', '1', '2']]
        ],
        [
            dell_eql_temp.EqlTemperature(
                item='MEMBER1.1',
                name='Backplane sensor 0',
                value=29,
                state=State.OK,
                levels_lower=(2, 1),
                levels_upper=(45, 50)
            )
        ]
    ),
])
def test_parse_dell_eql_temp(string_table, result):
    assert dell_eql_temp.parse_dell_eql_temp(string_table) == result


@pytest.mark.parametrize('section, result', [
    ([], []),
    (
        [
            dell_eql_temp.EqlTemperature(
                item='MEMBER1.1',
                name='Backplane sensor 0',
                value=29,
                state=State.OK,
                levels_lower=(2, 1),
                levels_upper=(45, 50)
            )
        ],
        [Service(item='MEMBER1.1')]
    ),
])
def test_discovery_dell_eql_temp(section, result):
    assert list(dell_eql_temp.discovery_dell_eql_temp(section)) == result


@pytest.mark.parametrize('item, params, section, result', [
    ('', {}, {}, []),
    (
        'foo', {},
        [
            dell_eql_temp.EqlTemperature(
                item='MEMBER1.1',
                name='Backplane sensor 0',
                value=29,
                state=State.OK,
                levels_lower=(2, 1),
                levels_upper=(45, 50)
            )
        ],
        []
    ),
    (
        'MEMBER1.1', {},
        [
            dell_eql_temp.EqlTemperature(
                item='MEMBER1.1',
                name='Backplane sensor 0',
                value=29,
                state=State.OK,
                levels_lower=(2, 1),
                levels_upper=(45, 50)
            )
        ],
        [
            Result(state=State.OK, summary='Backplane sensor 0'),
            Metric('temp', 29.0, levels=(45.0, 50.0)),
            Result(state=State.OK, summary='Temperature: 29 °C'),
            Result(state=State.OK, notice='State on device: None'),
            Result(state=State.OK, notice='Configuration: prefer user levels over device levels (used device levels)'),
        ]
    ),
])
def test_check_dell_eql_temp(monkeypatch, item, params, section, result):
    monkeypatch.setattr(dell_eql_temp, 'get_value_store', get_value_store)
    assert list(dell_eql_temp.check_dell_eql_temp(item, params, section)) == result


@pytest.mark.parametrize('params, result', [
    (
        {'levels': (24, 26)},
        Result(state=State.OK, summary='Temperature: 22 °C'),
    ),
    (
        {'levels': (18, 26)},
        Result(state=State.WARN, summary='Temperature: 22 °C (warn/crit at 18 °C/26 °C)'),
    ),
    (
        {'levels': (18, 20)},
        Result(state=State.CRIT, summary='Temperature: 22 °C (warn/crit at 18 °C/20 °C)'),
    ),
    (
        {'levels_lower': (20, 18)},
        Result(state=State.OK, summary='Temperature: 22 °C'),
    ),
    (
        {'levels_lower': (26, 18)},
        Result(state=State.WARN, summary='Temperature: 22 °C (warn/crit below 26 °C/18 °C)'),
    ),
    (
        {'levels_lower': (26, 24)},
        Result(state=State.CRIT, summary='Temperature: 22 °C (warn/crit below 26 °C/24 °C)'),
    ),
    (
        {'output_unit': 'c'},
        Result(state=State.OK, summary='Temperature: 22 °C'),
    ),
    (
        {'output_unit': 'f'},
        Result(state=State.OK, summary='Temperature: 71 °F'),
    ),
    (
        {'output_unit': 'k'},
        Result(state=State.OK, summary='Temperature: 295 K'),
    ),
])
def test_check_dell_eql_temp_w_param(monkeypatch, params, result):
    monkeypatch.setattr(dell_eql_temp, 'get_value_store', get_value_store)
    assert result in list(dell_eql_temp.check_dell_eql_temp('MEMBER1.1', params, [
        dell_eql_temp.EqlTemperature(
            item='MEMBER1.1',
            name='Backplane sensor 0',
            value=22,
            state=State.OK,
            levels_lower=(2, 1),
            levels_upper=(45, 50)
        )
    ]))

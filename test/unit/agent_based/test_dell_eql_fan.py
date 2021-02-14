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
from cmk.base.plugins.agent_based import dell_eql_fan

SAMPLE_STRING_TABLE = [
    [['1234567890', 'MEMBER1']],
    [
        ['1234567890.1', 'Power Cooling Module 0 Fan 0', '6000', '1', '14000', '13500', '3000', '3500'],
        ['1234567890.2', 'Power Cooling Module 0 Fan 1', '6000', '2', '14000', '13500', '3000', '3500']
    ],
]

SAMPLE_EQLFAN = [
    dell_eql_fan.EqlFan(
        item='MEMBER1.1',
        name='Power Cooling Module 0 Fan 0',
        value=6000,
        state=State.OK,
        levels_lower=(3500, 3000),
        levels_upper=(13500, 14000),
    ),
    dell_eql_fan.EqlFan(
        item='MEMBER1.2',
        name='Power Cooling Module 0 Fan 1',
        value=6000,
        state=State.WARN,
        levels_lower=(3500, 3000),
        levels_upper=(13500, 14000),
    )
]


@pytest.mark.parametrize('string_table, result', [
    (
        [[], []], []
    ),
    (
        SAMPLE_STRING_TABLE,
        SAMPLE_EQLFAN
    ),
])
def test_parse_dell_eql_fan(string_table, result):
    assert dell_eql_fan.parse_dell_eql_fan(string_table) == result


@pytest.mark.parametrize('section, result', [
    ([], []),
    (
        SAMPLE_EQLFAN,
        [Service(item=fan.item) for fan in SAMPLE_EQLFAN]
    ),
])
def test_discovery_dell_eql_fan(section, result):
    assert list(dell_eql_fan.discovery_dell_eql_fan(section)) == result


@pytest.mark.parametrize('item, params, section, result', [
    ('', {}, {}, []),
    (
        'foo', {},
        SAMPLE_EQLFAN,
        []
    ),
    (
        'MEMBER1.1', {},
        SAMPLE_EQLFAN,
        [
            Result(state=State.OK, summary='Power Cooling Module 0 Fan 0'),
            Result(state=State.OK, summary='Fan Speed: 6000.00'),
            Metric('fan', 6000.0, levels=(13500.0, 14000.0)),
        ]
    ),
    (
        'MEMBER1.2', {},
        SAMPLE_EQLFAN,
        [
            Result(state=State.WARN, summary='Power Cooling Module 0 Fan 1'),
            Result(state=State.OK, summary='Fan Speed: 6000.00'),
            Metric('fan', 6000.0, levels=(13500.0, 14000.0)),
        ]
    ),
])
def test_check_dell_eql_fan(monkeypatch, item, params, section, result):
    assert list(dell_eql_fan.check_dell_eql_fan(item, params, section)) == result


@pytest.mark.parametrize('params, result', [
    (
        {'lower': (2400, 1800)},
        Result(state=State.OK, summary='Fan Speed: 6000.00'),
    ),
    (
        {'lower': (7000, 1800)},
        Result(state=State.WARN, summary='Fan Speed: 6000.00 (warn/crit below 7000.00/1800.00)'),
    ),
    (
        {'lower': (7000, 7500)},
        Result(state=State.CRIT, summary='Fan Speed: 6000.00 (warn/crit below 7000.00/7500.00)'),
    ),
    (
        {'upper': (6500, 7000)},
        Result(state=State.OK, summary='Fan Speed: 6000.00'),
    ),
    (
        {'upper': (4000, 7000)},
        Result(state=State.WARN, summary='Fan Speed: 6000.00 (warn/crit at 4000.00/7000.00)'),
    ),
    (
        {'upper': (4000, 5000)},
        Result(state=State.CRIT, summary='Fan Speed: 6000.00 (warn/crit at 4000.00/5000.00)'),
    ),
])
def test_check_dell_eql_fan_w_param(monkeypatch, params, result):
    assert result in list(dell_eql_fan.check_dell_eql_fan('MEMBER1.1', params, SAMPLE_EQLFAN))

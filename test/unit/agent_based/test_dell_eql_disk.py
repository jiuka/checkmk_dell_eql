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
from cmk.base.plugins.agent_based import dell_eql_disk


def get_rate(_value_store, _key, _time, value):
    return value


SAMPLE_STRING_TABLE = [
    [['1234567890', 'MEMBER1'], ['1234567891', 'MEMBER2']],
    [
        ['1234567890.6', '1', '5', '1', '10676042', '12097'],
        ['1234567890.7', '2', '6', '2', '10676042', '12097'],
        ['1234567891.7', '2', '6', '2', '10676042', '12097'],
    ]
]

SAMPLE_PARSED = {
    'MEMBER1.6': {
        'read_throughput': 10676042,
        'slot': 5,
        'smart': 1,
        'status': 1,
        'write_throughput': 12097
    },
    'MEMBER1.7': {
        'read_throughput': 10676042,
        'slot': 6,
        'smart': 2,
        'status': 2,
        'write_throughput': 12097
    },
    'MEMBER2.7': {
        'read_throughput': 10676042,
        'slot': 6,
        'smart': 2,
        'status': 2,
        'write_throughput': 12097
    },
}


@pytest.mark.parametrize('string_table, result', [
    (
        [[], []], {}
    ),
    (
        SAMPLE_STRING_TABLE,
        SAMPLE_PARSED
    )
])
def test_parse_dell_eql_disk(string_table, result):
    assert dell_eql_disk.parse_dell_eql_disk(string_table) == result


@pytest.mark.parametrize('params, section, result', [
    ([{}], {}, []),
    (
        [{}],
        SAMPLE_PARSED,
        [
            Service(item='MEMBER1.6'),
            Service(item='MEMBER1.7'),
            Service(item='MEMBER2.7')
        ]
    ),
    (
        [{'summary': True}],
        SAMPLE_PARSED,
        [
            Service(item='SUMMARY MEMBER1'),
            Service(item='SUMMARY MEMBER2'),
        ]
    ),
])
def test_discovery_dell_eql_disk(params, section, result):
    assert list(dell_eql_disk.discovery_dell_eql_disk(params, section)) == result


@pytest.mark.parametrize('item, section, result', [
    ('', {}, []),
    (
        'foo',
        SAMPLE_PARSED,
        []
    ),
    (
        'MEMBER1.6',
        SAMPLE_PARSED,
        [
            Result(state=State.OK, notice='MEMBER1.6 Slot: 5 Status: on-line SMART: ok'),
            Result(state=State.OK, summary='Read: 10.7 MB/s'),
            Metric('disk_read_throughput', 10676042.0),
            Result(state=State.OK, summary='Write: 12.1 kB/s'),
            Metric('disk_write_throughput', 12097.0),
        ]
    ),
    (
        'SUMMARY MEMBER1',
        SAMPLE_PARSED,
        [
            Result(state=State.OK, notice='MEMBER1.6 Slot: 5 Status: on-line SMART: ok'),
            Result(state=State.WARN, summary='MEMBER1.7 Slot: 6 Status: spare SMART: tripped'),
            Result(state=State.OK, summary='Read: 21.4 MB/s'),
            Metric('disk_read_throughput', 21352084.0),
            Result(state=State.OK, summary='Write: 24.2 kB/s'),
            Metric('disk_write_throughput', 24194.0),
        ]
    ),
])
def test_check_dell_eql_disk(monkeypatch, item, section, result):
    monkeypatch.setattr(dell_eql_disk, 'get_rate', get_rate)
    assert list(dell_eql_disk.check_dell_eql_disk(item, {}, section)) == result


@pytest.mark.parametrize('params, result', [
    (
        {'read': (20, 30)},
        Result(state=State.OK, summary='Read: 10.7 MB/s')
    ),
    (
        {'read': (5, 30)},
        Result(state=State.WARN, summary='Read: 10.7 MB/s (warn/crit at 5.00 MB/s/30.0 MB/s)')
    ),
    (
        {'read': (5, 10)},
        Result(state=State.CRIT, summary='Read: 10.7 MB/s (warn/crit at 5.00 MB/s/10.0 MB/s)')
    ),
    (
        {'write': (1, 2)},
        Result(state=State.OK, summary='Write: 12.1 kB/s'),
    ),
    (
        {'write': (0.000008, 2)},
        Result(state=State.WARN, summary='Write: 12.1 kB/s (warn/crit at 8.00 B/s/2.00 MB/s)')
    ),
    (
        {'write': (0.000008, 0.000009)},
        Result(state=State.CRIT, summary='Write: 12.1 kB/s (warn/crit at 8.00 B/s/9.00 B/s)')
    ),
])
def test_check_dell_eql_disk_w_param(monkeypatch, params, result):
    monkeypatch.setattr(dell_eql_disk, 'get_rate', get_rate)
    assert result in list(dell_eql_disk.check_dell_eql_disk('MEMBER1.6', params, SAMPLE_PARSED))

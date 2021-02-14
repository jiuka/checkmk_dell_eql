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
from cmk.base.plugins.agent_based import dell_eql_volume


def get_rate(_value_store, _key, _time, value):
    return value


@pytest.mark.parametrize('string_table, result', [
    (
        [[], [], []], []
    ),
    (
        [
            [['1.2', 'Member1']],
            [['1.2', 'SAN-LUN0', '', '1', '1024000', '1', '1.2']],
            [['1.2', '10', '20', '30', '40', '50', '60']]
        ],
        [
            dell_eql_volume.EqlVolume(
                name='SAN-LUN0',
                desc='',
                status=1,
                access=1,
                size=1073741824000,
                pool='Member1',
                write_ios=50,
                read_ios=60,
                write_throughput=10,
                read_throughput=20,
                write_latency=30,
                read_latency=40
            )
        ]
    ),
])
def test_parse_dell_eql_volume(string_table, result):
    assert dell_eql_volume.parse_dell_eql_volume(string_table) == result


@pytest.mark.parametrize('section, result', [
    ([], []),
    (
        [
            dell_eql_volume.EqlVolume(
                name='SAN-LUN0',
                desc='',
                status=1,
                access=1,
                size=1073741824000,
                pool='Member1',
                write_ios=50,
                read_ios=60,
                write_throughput=10,
                read_throughput=20,
                write_latency=30,
                read_latency=40
            )
        ],
        [Service(item='SAN-LUN0', parameters={'adminStatus': 1, 'accessType': 1})]
    ),
])
def test_discovery_dell_eql_volume(section, result):
    assert list(dell_eql_volume.discovery_dell_eql_volume(section)) == result


@pytest.mark.parametrize('item, params, section, result', [
    ('', {}, {}, []),
    (
        'foo', {},
        [
            dell_eql_volume.EqlVolume(
                name='SAN-LUN0',
                desc='',
                status=1,
                access=1,
                size=1073741824000,
                pool='Member1',
                write_ios=50,
                read_ios=60,
                write_throughput=10,
                read_throughput=20,
                write_latency=30,
                read_latency=40
            )
        ],
        []
    ),
    (
        'SAN-LUN0', {'adminStatus': 1, 'accessType': 1},
        [
            dell_eql_volume.EqlVolume(
                name='SAN-LUN0',
                desc='',
                status=1,
                access=1,
                size=1073741824000,
                pool='Member1',
                write_ios=50,
                read_ios=60,
                write_throughput=10,
                read_throughput=20,
                write_latency=30,
                read_latency=40
            )
        ],
        [
            Result(state=State.OK, summary='Status: on-line'),
            Result(state=State.OK, summary='Access: read-write'),
            Result(state=State.OK, summary='Pool: Member1'),
            Result(state=State.OK, summary='Read: 20.0 B/s'),
            Metric('disk_read_throughput', 20.0),
            Result(state=State.OK, summary='Write: 10.0 B/s'),
            Metric('disk_write_throughput', 10.0),
            Result(state=State.OK, notice='Read operations: 60.00/s'),
            Metric('disk_read_ios', 60.0),
            Result(state=State.OK, notice='Write operations: 50.00/s'),
            Metric('disk_write_ios', 50.0),
            Result(state=State.OK, notice='Read latency: 40 seconds'),
            Metric('disk_read_latency', 40.0),
            Result(state=State.OK, notice='Write latency: 30 seconds'),
            Metric('disk_write_latency', 30.0),
        ]
    ),
    (
        'SAN-LUN0', {'adminStatus': 1, 'accessType': 1},
        [
            dell_eql_volume.EqlVolume(
                name='SAN-LUN0',
                desc='',
                status=2,
                access=2,
                size=1073741824000,
                pool='Member1',
                write_ios=50,
                read_ios=60,
                write_throughput=10,
                read_throughput=20,
                write_latency=30,
                read_latency=40
            )
        ],
        [
            Result(state=State.WARN, summary='Status: offline (expected: on-line)'),
            Result(state=State.WARN, summary='Access: read-only (expected: read-write)'),
            Result(state=State.OK, summary='Pool: Member1'),
            Result(state=State.OK, summary='Read: 20.0 B/s'),
            Metric('disk_read_throughput', 20.0),
            Result(state=State.OK, summary='Write: 10.0 B/s'),
            Metric('disk_write_throughput', 10.0),
            Result(state=State.OK, notice='Read operations: 60.00/s'),
            Metric('disk_read_ios', 60.0),
            Result(state=State.OK, notice='Write operations: 50.00/s'),
            Metric('disk_write_ios', 50.0),
            Result(state=State.OK, notice='Read latency: 40 seconds'),
            Metric('disk_read_latency', 40.0),
            Result(state=State.OK, notice='Write latency: 30 seconds'),
            Metric('disk_write_latency', 30.0),
        ]
    ),
    (
        'SAN-LUN0', {'adminStatus': 2, 'accessType': 2},
        [
            dell_eql_volume.EqlVolume(
                name='SAN-LUN0',
                desc='',
                status=2,
                access=2,
                size=1073741824000,
                pool='Member1',
                write_ios=50,
                read_ios=60,
                write_throughput=10,
                read_throughput=20,
                write_latency=30,
                read_latency=40
            )
        ],
        [
            Result(state=State.OK, summary='Status: offline'),
            Result(state=State.OK, summary='Access: read-only'),
            Result(state=State.OK, summary='Pool: Member1'),
            Result(state=State.OK, summary='Read: 20.0 B/s'),
            Metric('disk_read_throughput', 20.0),
            Result(state=State.OK, summary='Write: 10.0 B/s'),
            Metric('disk_write_throughput', 10.0),
            Result(state=State.OK, notice='Read operations: 60.00/s'),
            Metric('disk_read_ios', 60.0),
            Result(state=State.OK, notice='Write operations: 50.00/s'),
            Metric('disk_write_ios', 50.0),
            Result(state=State.OK, notice='Read latency: 40 seconds'),
            Metric('disk_read_latency', 40.0),
            Result(state=State.OK, notice='Write latency: 30 seconds'),
            Metric('disk_write_latency', 30.0),
        ]
    ),
    (
        'SAN-LUN0', {'adminStatus': 1, 'accessType': 1, 'read_iop': (5, 20)},
        [
            dell_eql_volume.EqlVolume(
                name='SAN-LUN0',
                desc='',
                status=1,
                access=1,
                size=1073741824000,
                pool='Member1',
                write_ios=50,
                read_ios=60,
                write_throughput=10,
                read_throughput=20,
                write_latency=30,
                read_latency=40
            )
        ],
        [
            Result(state=State.OK, summary='Status: on-line'),
            Result(state=State.OK, summary='Access: read-write'),
            Result(state=State.OK, summary='Pool: Member1'),
            Result(state=State.OK, summary='Read: 20.0 B/s'),
            Metric('disk_read_throughput', 20.0),
            Result(state=State.OK, summary='Write: 10.0 B/s'),
            Metric('disk_write_throughput', 10.0),
            Result(state=State.OK, notice='Read operations: 60.00/s'),
            Metric('disk_read_ios', 60.0),
            Result(state=State.OK, notice='Write operations: 50.00/s'),
            Metric('disk_write_ios', 50.0),
            Result(state=State.OK, notice='Read latency: 40 seconds'),
            Metric('disk_read_latency', 40.0),
            Result(state=State.OK, notice='Write latency: 30 seconds'),
            Metric('disk_write_latency', 30.0),
        ]
    ),
])
def test_check_dell_eql_volume(monkeypatch, item, params, section, result):
    monkeypatch.setattr(dell_eql_volume, 'get_rate', get_rate)
    assert list(dell_eql_volume.check_dell_eql_volume(item, params, section)) == result


@pytest.mark.parametrize('params, result', [
    (
        {'read': (1, 2)},
        Result(state=State.OK, summary='Read: 20.0 B/s')
    ),
    (
        {'read': (0.000008, 2)},
        Result(state=State.WARN, summary='Read: 20.0 B/s (warn/crit at 8.00 B/s/2.00 MB/s)')
    ),
    (
        {'read': (0.000008, 0.000009)},
        Result(state=State.CRIT, summary='Read: 20.0 B/s (warn/crit at 8.00 B/s/9.00 B/s)')
    ),
    (
        {'write': (1, 2)},
        Result(state=State.OK, summary='Write: 10.0 B/s')
    ),
    (
        {'write': (0.000008, 2)},
        Result(state=State.WARN, summary='Write: 10.0 B/s (warn/crit at 8.00 B/s/2.00 MB/s)')
    ),
    (
        {'write': (0.000008, 0.000009)},
        Result(state=State.CRIT, summary='Write: 10.0 B/s (warn/crit at 8.00 B/s/9.00 B/s)')
    ),
    (
        {'read_ios': (70, 80)},
        Result(state=State.OK, notice='Read operations: 60.00/s'),
    ),
    (
        {'read_ios': (40, 80)},
        Result(state=State.WARN, notice='Read operations: 60.00/s (warn/crit at 40.00/s/80.00/s)'),
    ),
    (
        {'read_ios': (40, 50)},
        Result(state=State.CRIT, notice='Read operations: 60.00/s (warn/crit at 40.00/s/50.00/s)'),
    ),
    (
        {'write_ios': (60, 70)},
        Result(state=State.OK, notice='Write operations: 50.00/s'),
    ),
    (
        {'write_ios': (30, 70)},
        Result(state=State.WARN, notice='Write operations: 50.00/s (warn/crit at 30.00/s/70.00/s)'),
    ),
    (
        {'write_ios': (30, 40)},
        Result(state=State.CRIT, notice='Write operations: 50.00/s (warn/crit at 30.00/s/40.00/s)'),
    ),
    (
        {'read_latency': (50000, 60000)},
        Result(state=State.OK, notice='Read latency: 40 seconds'),
    ),
    (
        {'read_latency': (20000, 60000)},
        Result(state=State.WARN, notice='Read latency: 40 seconds (warn/crit at 20 seconds/1 minute 0 seconds)'),
    ),
    (
        {'read_latency': (20000, 30000)},
        Result(state=State.CRIT, notice='Read latency: 40 seconds (warn/crit at 20 seconds/30 seconds)'),
    ),
    (
        {'write_latency': (35000, 40000)},
        Result(state=State.OK, notice='Write latency: 30 seconds'),
    ),
    (
        {'write_latency': (10000, 40000)},
        Result(state=State.WARN, notice='Write latency: 30 seconds (warn/crit at 10 seconds/40 seconds)'),
    ),
    (
        {'write_latency': (10000, 20000)},
        Result(state=State.CRIT, notice='Write latency: 30 seconds (warn/crit at 10 seconds/20 seconds)'),
    ),
])
def test_check_dell_eql_volume_w_param(monkeypatch, params, result):
    monkeypatch.setattr(dell_eql_volume, 'get_rate', get_rate)
    params.update({'adminStatus': 2, 'accessType': 2})
    for i in list(dell_eql_volume.check_dell_eql_volume('SAN-LUN0', params, [
        dell_eql_volume.EqlVolume(
            name='SAN-LUN0',
            desc='',
            status=1,
            access=1,
            size=1073741824000,
            pool='Member1',
            write_ios=50,
            read_ios=60,
            write_throughput=10,
            read_throughput=20,
            write_latency=30,
            read_latency=40
        )
    ])):
        print(i)
    assert result in list(dell_eql_volume.check_dell_eql_volume('SAN-LUN0', params, [
        dell_eql_volume.EqlVolume(
            name='SAN-LUN0',
            desc='',
            status=1,
            access=1,
            size=1073741824000,
            pool='Member1',
            write_ios=50,
            read_ios=60,
            write_throughput=10,
            read_throughput=20,
            write_latency=30,
            read_latency=40
        )
    ]))

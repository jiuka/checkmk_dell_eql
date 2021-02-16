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

# Example excerpt from SNMP data
# .1.3.6.1.4.1.12740.5.1.7.1.1.4.1234567890.47 VM-Test01 --> EQLVOLUME-MIB::eqliscsiVolumeName
# .1.3.6.1.4.1.12740.5.1.7.1.1.6.1234567890.47 --> EQLVOLUME-MIB::eqliscsiVolumeDescription
# .1.3.6.1.4.1.12740.5.1.7.1.1.7.1234567890.47 1 --> EQLVOLUME-MIB::eqliscsiVolumeAccessType
# .1.3.6.1.4.1.12740.5.1.7.1.1.8.1234567890.47 6291456 --> EQLVOLUME-MIB::eqliscsiVolumeSize
# .1.3.6.1.4.1.12740.5.1.7.1.1.9.1234567890.47 1 --> EQLVOLUME-MIB::eqliscsiVolumeAdminStatus
# .1.3.6.1.4.1.12740.5.1.7.1.1.22.1234567890.47 1 --> EQLVOLUME-MIB::eqliscsiVolumeStoragePoolIndex
# .1.3.6.1.4.1.12740.5.1.7.34.1.3.1234567890.47 56830743714816 --> EQLVOLUME-MIB::eqliscsiVolumeStatsTxData
# .1.3.6.1.4.1.12740.5.1.7.34.1.4.1234567890.47 114570381047808 --> EQLVOLUME-MIB::eqliscsiVolumeStatsRxData
# .1.3.6.1.4.1.12740.5.1.7.34.1.6.1234567890.47 2442383417676 --> EQLVOLUME-MIB::eqliscsiVolumeStatsReadLatency
# .1.3.6.1.4.1.12740.5.1.7.34.1.7.1234567890.47 460868171358 --> EQLVOLUME-MIB::eqliscsiVolumeStatsWriteLatency
# .1.3.6.1.4.1.12740.5.1.7.34.1.8.1234567890.47 2160473721 --> EQLVOLUME-MIB::eqliscsiVolumeStatsReadOpCount
# .1.3.6.1.4.1.12740.5.1.7.34.1.9.1234567890.47 4241488288 --> EQLVOLUME-MIB::eqliscsiVolumeStatsWriteOpCount


from typing import NamedTuple
import time
from contextlib import suppress
from .agent_based_api.v1 import (
    exists,
    get_rate,
    get_value_store,
    GetRateError,
    OIDEnd,
    register,
    Result,
    Service,
    SNMPTree,
    State,
)
from .utils import diskstat


class EqlVolume(NamedTuple):
    name: str
    desc: str
    status: int
    access: int
    size: int
    pool: str
    write_ios: int
    read_ios: int
    write_throughput: int
    read_throughput: int
    write_latency: int
    read_latency: int


def parse_dell_eql_volume(string_table):
    parsed = []

    pools, vol, volstats = string_table

    poolname = dict(pools)
    volstats = dict([(v[0], v[1:]) for v in volstats])

    for idx, name, desc, access, size, status, pool in vol:
        parsed.append(
            EqlVolume(
                name=name,
                desc=desc,
                status=int(status),
                access=int(access),
                size=int(size) * 1024 * 1024,
                pool=poolname[pool],
                write_throughput=int(volstats[idx][0]),
                read_throughput=int(volstats[idx][1]),
                write_latency=int(volstats[idx][2]),
                read_latency=int(volstats[idx][3]),
                write_ios=int(volstats[idx][4]),
                read_ios=int(volstats[idx][5]),
            )
        )
    return parsed


register.snmp_section(
    name='dell_eql_volume',
    detect=exists('.1.3.6.1.4.1.12740.5.*'),
    fetch=[
        SNMPTree(
            base=".1.3.6.1.4.1.12740.16.1.1.1.3",
            oids=[
                OIDEnd(),
                '1',   # EQLSTORAGEPOOL-MIB::eqlStoragePoolName
            ]
        ),
        SNMPTree(
            base='.1.3.6.1.4.1.12740.5.1.7.1.1',
            oids=[
                OIDEnd(),
                '4',   # EQLVOLUME-MIB::eqliscsiVolumeName
                '6',   # EQLVOLUME-MIB::eqliscsiVolumeDescription
                '7',   # EQLVOLUME-MIB::eqliscsiVolumeAccessType
                '8',   # EQLVOLUME-MIB::eqliscsiVolumeSize
                '9',   # EQLVOLUME-MIB::eqliscsiVolumeAdminStatus
                '22',  # EQLVOLUME-MIB::eqliscsiVolumeStoragePoolIndex
            ],
        ),
        SNMPTree(
            base='.1.3.6.1.4.1.12740.5.1.7.34.1',
            oids=[
                OIDEnd(),
                '3',   # EQLVOLUME-MIB::eqliscsiVolumeStatsTxData
                '4',   # EQLVOLUME-MIB::eqliscsiVolumeStatsRxData
                '6',   # EQLVOLUME-MIB::eqliscsiVolumeStatsReadLatency
                '7',   # EQLVOLUME-MIB::eqliscsiVolumeStatsWriteLatency
                '8',   # EQLVOLUME-MIB::eqliscsiVolumeStatsReadOpCount
                '9',   # EQLVOLUME-MIB::eqliscsiVolumeStatsWriteOpCount
            ],
        ),
    ],
    parse_function=parse_dell_eql_volume,
)

DELL_EQL_VOLUME_STATUS = {
    1: 'on-line',
    2: 'offline',
    3: 'online-lost-cached-blocks',
    4: 'online-control',
    5: 'offline-control',
}

DELL_EQL_VOLUME_ACCESS = {
    1: 'read-write',
    2: 'read-only',
}


def discovery_dell_eql_volume(section):
    for vol in section:
        yield Service(item=vol.name, parameters={'adminStatus': vol.status, 'accessType': vol.access})


def check_dell_eql_volume(item, params, section):
    for vol in section:
        if not item == vol.name:
            continue

        if params['adminStatus'] == vol.status:
            yield Result(state=State.OK, summary=f'Status: {DELL_EQL_VOLUME_STATUS[vol.status]}')
        else:
            yield Result(state=State.WARN, summary=f'Status: {DELL_EQL_VOLUME_STATUS[vol.status]} (expected: {DELL_EQL_VOLUME_STATUS[params["adminStatus"]]})')

        if params['accessType'] == vol.access:
            yield Result(state=State.OK, summary=f'Access: {DELL_EQL_VOLUME_ACCESS[vol.access]}')
        else:
            yield Result(state=State.WARN, summary=f'Access: {DELL_EQL_VOLUME_ACCESS[vol.access]} (expected: {DELL_EQL_VOLUME_ACCESS[params["accessType"]]})')

        if vol.desc:
            yield Result(state=State.OK, summary=f'Description: {vol.desc}')
        yield Result(state=State.OK, summary=f'Pool: {vol.pool}')

        disk = {}
        value_store = get_value_store()
        for key in ['read_ios', 'read_throughput', 'read_latency', 'write_ios', 'write_throughput', 'write_latency']:
            with suppress(GetRateError):
                disk[key] = get_rate(value_store,
                                     'check_dell_eql_volume.%s.%s' % (item, key),
                                     time.time(),
                                     getattr(vol, key))

        yield from diskstat.check_diskstat_dict(
            params=params,
            disk=disk,
            value_store=value_store,
            this_time=time.time(),
        )


register.check_plugin(
    name='dell_eql_volume',
    service_name='Volume %s',
    discovery_function=discovery_dell_eql_volume,
    check_function=check_dell_eql_volume,
    check_ruleset_name='diskstat',
    check_default_parameters={},
)

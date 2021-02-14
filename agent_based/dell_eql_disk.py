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
# .1.3.6.1.4.1.12740.2.1.1.1.9.1.1234567890 MEMBER1 --> EQLMEMBER-MIB::eqlMemberName
# .1.3.6.1.4.1.12740.3.1.1.1.8.1.1234567890.6 1 --> EQLDISK-MIB::eqlDiskStatus
# .1.3.6.1.4.1.12740.3.1.1.1.11.1.1234567890.6 5 --> EQLDISK-MIB::eqlDiskSlot
# .1.3.6.1.4.1.12740.3.1.1.1.17.1.1234567890.6 1 --> EQLDISK-MIB::eqlDiskHealth
# .1.3.6.1.4.1.12740.3.1.2.1.2.1.1234567890.6 10676042 --> EQLDISK-MIB::eqlDiskStatusBytesRead
# .1.3.6.1.4.1.12740.3.1.2.1.3.1.1234567890.6 12097 --> EQLDISK-MIB::eqlDiskStatusBytesWritten


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


def parse_dell_eql_disk(string_table):
    members, disks = string_table
    membername = dict(members)

    parsed = {}

    for idx, status, slot, smart, read_throughput, write_throughput in disks:
        member, midx = idx.rsplit('.', 1)
        name = f'{membername.get(member)}.{midx}'

        parsed[name] = {
            'status': int(status),
            'slot': int(slot),
            'smart': int(smart),
            'read_throughput': int(read_throughput),
            'write_throughput': int(write_throughput),
        }

    return parsed


register.snmp_section(
    name='dell_eql_disk',
    detect=exists('.1.3.6.1.4.1.12740.3.1.*'),
    fetch=[
        SNMPTree(
            base='.1.3.6.1.4.1.12740.2.1.1.1',
            oids=[
                OIDEnd(),
                '9',  # EQLMEMBER-MIB::eqlMemberName
            ]
        ),
        SNMPTree(
            base='.1.3.6.1.4.1.12740.3.1',
            oids=[
                OIDEnd(),
                '1.1.8',   # EQLDISK-MIB::eqlDiskStatus
                '1.1.11',  # EQLDISK-MIB::eqlDiskSlot
                '1.1.17',   # EQLDISK-MIB::eqlDiskHealth
                '2.1.2',   # EQLDISK-MIB::eqlDiskStatusBytesRead
                '2.1.3',   # EQLDISK-MIB::eqlDiskStatusBytesWritten
            ],
        ),
    ],
    parse_function=parse_dell_eql_disk,
)

DELL_EQL_DISK_STATUS = {
    1: (State.OK, 'on-line'),
    2: (State.OK, 'spare'),
    3: (State.CRIT, 'failed'),
    4: (State.WARN, 'off-line'),
    5: (State.CRIT, 'alt-sig'),
    6: (State.CRIT, 'too-small'),
    7: (State.CRIT, 'history-of-failures'),
    8: (State.CRIT, 'unsupported-version'),
    9: (State.CRIT, 'unhealthy'),
    10: (State.CRIT, 'replacement'),
    11: (State.CRIT, 'encrypted'),
    12: (State.CRIT, 'notApproved'),
    13: (State.CRIT, 'preempt-failed'),
}
DELL_EQL_DISK_SMART_STATUS = {
    0: (State.UNKNOWN, 'not available'),
    1: (State.OK, 'ok'),
    2: (State.WARN, 'tripped'),
}


def discovery_dell_eql_disk(params, section):
    if 'summary' in params[0]:
        for member in set([disk.rsplit('.', 1)[0] for disk in section.keys()]):
            yield Service(item=f'SUMMARY {member}')
    else:
        for disk in section.keys():
            yield Service(item=f'{disk}')


def check_dell_eql_single_disk(name, disk):
    admin_state, admin_str = DELL_EQL_DISK_STATUS.get(disk['status'], (State.UNKNOWN, 'Unknown state'))
    smart_state, smart_str = DELL_EQL_DISK_SMART_STATUS.get(disk['smart'], (State.UNKNOWN, 'Unknown state'))

    yield Result(
        state=State.worst(admin_state, smart_state),
        notice=f'{name} Slot: {disk["slot"]} Status: {admin_str} SMART: {smart_str}')


def check_dell_eql_disk(item, params, section):
    stat = {
        'read_throughput': 0,
        'write_throughput': 0
    }

    if item.startswith('SUMMARY '):
        for name, value in section.items():
            if not name.startswith(item[8:]):
                continue

            yield from check_dell_eql_single_disk(name, value)

            stat['read_throughput'] += value['read_throughput']
            stat['write_throughput'] += value['write_throughput']

    else:
        for name, value in section.items():
            if not name == item:
                continue

            yield from check_dell_eql_single_disk(name, value)

            stat['read_throughput'] = value['read_throughput']
            stat['write_throughput'] = value['write_throughput']

    value_store = get_value_store()
    for key in ['read_throughput', 'write_throughput']:
        with suppress(GetRateError):
            stat[key] = get_rate(value_store,
                                 'dell_eql_disk.%s.%s' % (item, key),
                                 time.time(),
                                 stat[key])

    yield from diskstat.check_diskstat_dict(
        params=params,
        disk=stat,
        value_store=value_store,
        this_time=time.time(),
    )


register.check_plugin(
    name='dell_eql_disk',
    service_name='Disk IO %s',
    discovery_ruleset_name="diskstat_inventory",
    discovery_ruleset_type=register.RuleSetType.ALL,
    discovery_default_parameters={'summary': True},
    discovery_function=discovery_dell_eql_disk,
    check_ruleset_name='diskstat',
    check_default_parameters={},
    check_function=check_dell_eql_disk,
)

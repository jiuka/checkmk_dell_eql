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
# .1.3.6.1.4.1.12740.2.1.7.1.2.1.1234567890.1 Power Cooling Module 0 Fan 0 --> EQLMEMBER-MIB::eqlMemberHealthDetailsFanName
# .1.3.6.1.4.1.12740.2.1.7.1.3.1.1234567890.1 6000 --> EQLMEMBER-MIB::eqlMemberHealthDetailsFanValue
# .1.3.6.1.4.1.12740.2.1.7.1.4.1.1234567890.1 1 --> EQLMEMBER-MIB::eqlMemberHealthDetailsFanCurrentState
# .1.3.6.1.4.1.12740.2.1.7.1.5.1.1234567890.1 14000 --> EQLMEMBER-MIB::eqlMemberHealthDetailsFanHighCriticalThreshold
# .1.3.6.1.4.1.12740.2.1.7.1.6.1.1234567890.1 13500 --> EQLMEMBER-MIB::eqlMemberHealthDetailsFanHighWarningThreshold
# .1.3.6.1.4.1.12740.2.1.7.1.7.1.1234567890.1 3000 --> EQLMEMBER-MIB::eqlMemberHealthDetailsFanLowCriticalThreshold
# .1.3.6.1.4.1.12740.2.1.7.1.8.1.1234567890.1 3500 --> EQLMEMBER-MIB::eqlMemberHealthDetailsFanLowWarningThreshold
# .1.3.6.1.4.1.12740.2.1.7.1.9.1.1234567890.1 117964884 --> EQLMEMBER-MIB::eqlMemberHealthDetailsFanNameID


from typing import NamedTuple, Tuple
from .agent_based_api.v1 import (
    check_levels,
    exists,
    OIDEnd,
    register,
    Result,
    Service,
    SNMPTree,
    State,
)


class EqlFan(NamedTuple):
    item: str
    name: str
    value: int
    state: int
    levels_lower: Tuple[int, int]
    levels_upper: Tuple[int, int]


def parse_dell_eql_fan(string_table):
    parsed = []

    members, temps = string_table
    membername = dict(members)

    for idx, name, value, state, upper_crit, upper_warn, lower_crit, lower_warn in temps:
        member, midx = idx.rsplit('.', 1)
        parsed.append(
            EqlFan(
                item=f'{membername.get(member)}.{midx}',
                name=name,
                value=int(value),
                state=State((int(state) - 1) % 4),
                levels_lower=(int(lower_warn), int(lower_crit)),
                levels_upper=(int(upper_warn), int(upper_crit)),
            )
        )
    return parsed


register.snmp_section(
    name='dell_eql_fan',
    detect=exists('.1.3.6.1.4.1.12740.2.1.7.1.*'),
    fetch=[
        SNMPTree(
            base='.1.3.6.1.4.1.12740.2.1.1.1',
            oids=[
                OIDEnd(),
                '9',  # EQLMEMBER-MIB::eqlMemberName
            ]
        ),
        SNMPTree(
            base='.1.3.6.1.4.1.12740.2.1.7.1',
            oids=[
                OIDEnd(),
                '2',  # EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureName
                '3',  # EQLMEMBER-MIB::eqlMemberHealthDetailsFanValue
                '4',  # EQLMEMBER-MIB::eqlMemberHealthDetailsFanCurrentState
                '5',  # EQLMEMBER-MIB::eqlMemberHealthDetailsFanHighCriticalThreshold
                '6',  # EQLMEMBER-MIB::eqlMemberHealthDetailsFanHighWarningThreshold
                '7',  # EQLMEMBER-MIB::eqlMemberHealthDetailsFanLowCriticalThreshold
                '8',  # EQLMEMBER-MIB::eqlMemberHealthDetailsFanLowWarningThreshold
            ],
        ),
    ],
    parse_function=parse_dell_eql_fan,
)


def discovery_dell_eql_fan(section):
    for fan in section:
        yield Service(item=fan.item)


def check_dell_eql_fan(item, params, section):
    for fan in section:
        if not item == fan.item:
            continue

        yield Result(state=fan.state, summary=fan.name)

        yield from check_levels(
            value=fan.value,
            metric_name='fan' if params.get('output_metrics', True) else None,
            levels_lower=params.get('lower', fan.levels_lower),
            levels_upper=params.get('upper', fan.levels_upper),
            label='Fan Speed',
        )


register.check_plugin(
    name='dell_eql_fan',
    service_name='FAN %s',
    discovery_function=discovery_dell_eql_fan,
    check_function=check_dell_eql_fan,
    check_ruleset_name='hw_fans',
    check_default_parameters={},
)

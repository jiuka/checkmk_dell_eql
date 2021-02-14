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
# .1.3.6.1.4.1.12740.2.1.1.1.9.1.1234567890 MEMBER1 --> EQLMEMBER-MIB::eqlMemberName
# .1.3.6.1.4.1.12740.2.1.6.1.2.1.1234567890.2 Backplane sensor 0 --> EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureName
# .1.3.6.1.4.1.12740.2.1.6.1.3.1.1234567890.2 29 --> EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureValue
# .1.3.6.1.4.1.12740.2.1.6.1.4.1.1234567890.2 1 --> EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureCurrentState
# .1.3.6.1.4.1.12740.2.1.6.1.5.1.1234567890.2 50 --> EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureHighCriticalThreshold
# .1.3.6.1.4.1.12740.2.1.6.1.6.1.1234567890.2 45 --> EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureHighWarningThreshold
# .1.3.6.1.4.1.12740.2.1.6.1.7.1.1234567890.2 1 --> EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureLowCriticalThreshold
# .1.3.6.1.4.1.12740.2.1.6.1.8.1.1234567890.2 2 --> EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureLowWarningThreshold
# .1.3.6.1.4.1.12740.2.1.6.1.9.1.1234567890.2 117964848 --> EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureNameID


from typing import NamedTuple, Tuple
from .agent_based_api.v1 import (
    exists,
    OIDEnd,
    register,
    Result,
    Service,
    SNMPTree,
    State,
)
from .utils.temperature import (
    check_temperature,
)


class EqlTemperature(NamedTuple):
    item: str
    name: str
    value: int
    state: int
    levels_lower: Tuple[int, int]
    levels_upper: Tuple[int, int]


def parse_dell_eql_temp(string_table):
    parsed = []

    members, temps = string_table
    membername = dict(members)

    for idx, name, value, state, upper_crit, upper_warn, lower_crit, lower_warn in temps:
        member, midx = idx.rsplit('.', 1)
        parsed.append(
            EqlTemperature(
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
    name='dell_eql_temp',
    detect=exists('.1.3.6.1.4.1.12740.2.1.6.1.*'),
    fetch=[
        SNMPTree(
            base='.1.3.6.1.4.1.12740.2.1.1.1',
            oids=[
                OIDEnd(),
                '9',  # EQLMEMBER-MIB::eqlMemberName
            ]
        ),
        SNMPTree(
            base='.1.3.6.1.4.1.12740.2.1.6.1',
            oids=[
                OIDEnd(),
                '2',  # EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureName
                '3',  # EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureValue
                '4',  # EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureCurrentState
                '5',  # EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureHighCriticalThreshold
                '6',  # EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureHighWarningThreshold
                '7',  # EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureLowCriticalThreshold
                '8',  # EQLMEMBER-MIB::eqlMemberHealthDetailsTemperatureLowWarningThreshold
            ],
        ),
    ],
    parse_function=parse_dell_eql_temp,
)


def discovery_dell_eql_temp(section):
    for temp in section:
        yield Service(item=temp.item)


def check_dell_eql_temp(item, params, section):
    for temp in section:
        if not item == temp.item:
            continue

        yield Result(state=State.OK, summary=temp.name)

        yield from check_temperature(
            reading=temp.value,
            params=params,
            unique_name="dell_eql_temp.%s" % item,
            dev_levels= temp.levels_upper,
            dev_levels_lower = temp.levels_lower,
            dev_status=temp.state
        )


register.check_plugin(
    name='dell_eql_temp',
    service_name='Temperature %s',
    discovery_function=discovery_dell_eql_temp,
    check_function=check_dell_eql_temp,
    check_ruleset_name='temp',
    check_default_parameters={},
)

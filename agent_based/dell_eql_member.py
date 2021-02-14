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
# .1.3.6.1.4.1.12740.2.1.5.1.1.1.1234567890 2 --> EQLMEMBER-MIB::eqlMemberHealthStatus
# .1.3.6.1.4.1.12740.2.1.5.1.1.1.1234567891 1 --> EQLMEMBER-MIB::eqlMemberHealthStatus
# .1.3.6.1.4.1.12740.2.1.5.1.2.1.1234567890 '00 00 00 01 00 00 00 00 00 00 00 00 00 00 00 00 ' --> EQLMEMBER-MIB::eqlMemberHealthWarningConditions
# .1.3.6.1.4.1.12740.2.1.5.1.2.1.1234567891 '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ' --> EQLMEMBER-MIB::eqlMemberHealthWarningConditions
# .1.3.6.1.4.1.12740.2.1.5.1.3.1.1234567890 '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ' --> EQLMEMBER-MIB::eqlMemberHealthCriticalConditions
# .1.3.6.1.4.1.12740.2.1.5.1.3.1.1234567891 '00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 ' --> EQLMEMBER-MIB::eqlMemberHealthCriticalConditions


from typing import NamedTuple
from .agent_based_api.v1 import (
    exists,
    Metric,
    OIDBytes,
    register,
    render,
    Result,
    Service,
    SNMPTree,
    State,
)
from cmk.gui.plugins.metrics import MB


class EqlMember(NamedTuple):
    name: str
    desc: str
    health: int
    warnings: list
    critical: list
    raid: int
    storage: int
    repl: int
    snap: int
    used: int


DELL_EQL_WARNING_CONDITIONS = (
    'hwComponentFailedWarn',
    'powerSupplyRemoved',
    'controlModuleRemoved',
    'psfanOffline',
    'fanSpeed',
    'cacheSyncing',
    'raidSetFaulted',
    'highTemp',
    'raidSetLostblkEntry',
    'secondaryEjectSWOpen',
    'b2bFailure',
    'replicationNoProg',
    'raidSpareTooSmall',
    'lowTemp',
    'powerSupplyFailed',
    'timeOfDayClkBatteryLow',
    'incorrectPhysRamSize',
    'enclosureOpenTemp',
    'sumoChannelCardMissing',
    'sumoChannelCardFailed',
    'batteryLessthan72hours',
    'cpuFanNotSpinning',
    'raidMoreSparesExpected',
    'raidSpareWrongType',
    'raidSsdRaidsetHasHdd',
    'driveNotApproved',
    'warnbit26',
    'warnbit27',
    'warnbit28',
    'warnbit29',
    'warnbit30',
    'warnbit31',
)
DELL_EQL_CRITICAL_CONDITIONS = (
    'raidSetDoubleFaulted',
    'bothFanTraysRemoved',
    'highAmbientTemp',
    'raidLostCache',
    'moreThanOneFanSpeedCondition',
    'fanTrayRemoved',
    'raidSetLostblkTableFull',
    'critbit7',
    'raidOrphanCache',
    'raidMultipleRaidSets',
    'nVRAMBatteryFailed',
    'hwComponentFailedCrit',
    'incompatControlModule',
    'lowAmbientTemp',
    'opsPanelFailure',
    'emmLinkFailure',
    'highBatteryTemperature',
    'enclosureOpenPerm',
    'sumoChannelBothMissing',
    'sumoEIPFailureCOndition',
    'sumoChannelBothFailed',
    'staleMirrorDiskFailure',
    'c2fPowerModuleFailureCondition',
    'critbit23',
    'critbit24',
    'critbit25',
    'critbit26',
    'critbit27',
    'critbit28',
    'critbit29',
    'critbit30',
    'critbit31'
)


def get_conditions(conditions, bytelist):
    for idx in range(len(conditions)):
        byte = int(idx / 4)
        value = 0b11000000 >> (2 * (idx % 4))

        if bytelist[byte] & value:
            yield conditions[idx]


def parse_dell_eql_member(string_table):
    parsed = []

    for name, desc, health, warnings, critical, raid, storage, repl, snap, used in string_table:
        parsed.append(
            EqlMember(
                name=name,
                desc=desc,
                health=State((int(health) - 1) % 4),
                warnings=list(get_conditions(DELL_EQL_WARNING_CONDITIONS, warnings)),
                critical=list(get_conditions(DELL_EQL_CRITICAL_CONDITIONS, critical)),
                raid=int(raid),
                storage=int(storage) * MB,
                repl=int(repl) * MB,
                snap=int(snap) * MB,
                used=int(used) * MB,
            )
        )
    return parsed


register.snmp_section(
    name='dell_eql_member',
    detect=exists('.1.3.6.1.4.1.12740.2.1.1.1.9.1.*'),
    fetch=SNMPTree(
        base='.1.3.6.1.4.1.12740.2.1',
        oids=[
            '1.1.9.1',   # EQLMEMBER-MIB::eqlMemberName
            '1.1.7.1',   # EQLMEMBER-MIB::eqlMemberDescription
            '5.1.1.1',   # EQLMEMBER-MIB::eqlMemberHealthStatus
            OIDBytes('5.1.2.1'),   # EQLMEMBER-MIB::eqlMemberHealthWarningConditions
            OIDBytes('5.1.3.1'),   # EQLMEMBER-MIB::eqlMemberHealthCriticalConditions
            '13.1.1.1',  # EQLMEMBER-MIB::eqlMemberRaidStatus
            '10.1.1.1',  # EQLMEMBER-MIB::eqlMemberTotalStorage
            '10.1.4.1',  # EQLMEMBER-MIB::eqlMemberReplStorage
            '10.1.3.1',  # EQLMEMBER-MIB::eqlMemberSnapStorage
            '10.1.2.1',  # EQLMEMBER-MIB::eqlMemberUsedStorage
        ],
    ),
    parse_function=parse_dell_eql_member,
    supersedes=['dell_eql_storage'],
)


DELL_EQL_RAID_STATES = {
    1: 'Ok',
    2: 'Degraded',
    3: 'Verifying',
    4: 'Reconstructing',
    5: 'Failed',
    6: 'CatastrophicLoss',
    7: 'Expanding',
    8: 'Mirroring',
}


def discovery_dell_eql_member(section):
    for member in section:
        yield Service(item=member.name)


def check_dell_eql_member(item, section):
    for member in section:
        if not item == member.name:
            continue

        if member.desc:
            yield Result(state=State.OK, summary=member.desc)

        # Health
        yield Result(state=member.health, notice=f'Health State: {member.health}')
        if member.warnings:
            yield Result(state=State.WARN, summary=f'Warn: {" ".join(member.warnings)}')
        if member.critical:
            yield Result(state=State.CRIT, summary=f'Crit: {" ".join(member.critical)}')

        # RAID
        if member.raid == 1:
            state = State.OK
        elif member.raid in [3, 4, 7, 8]:
            state = State.WARN
        else:
            state = State.CRIT
        yield Result(state=state, notice=f'Raid State: {DELL_EQL_RAID_STATES[member.raid]}')

        yield Result(state=State.OK, summary='Used: %s/%s (Snapshots: %s, Replication: %s)' % (
            render.disksize(member.used), render.disksize(member.storage),
            render.disksize(member.snap), render.disksize(member.repl),
        ))

        yield Metric('fs_used', member.used)
        yield Metric('fs_size', member.storage)


register.check_plugin(
    name='dell_eql_member',
    service_name='Storage %s',
    discovery_function=discovery_dell_eql_member,
    check_function=check_dell_eql_member,
)

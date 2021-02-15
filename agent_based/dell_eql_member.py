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
from functools import reduce
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
    'hwComponentFailedWarn',    # (0), -- A non-critical hardware component has failed
    'powerSupplyRemoved',       # (1), -- One of the power supplys has been removed;
    'controlModuleRemoved',     # (2), -- a cm is missing....
    'psfanOffline',             # (3), -- a power supply fan has failed;
    'fanSpeed',                 # (4), -- a fan is not operating in its normal ranges;
                                #      -- check the eqllog msgs to see the exact fan and issue
    'cacheSyncing',             # (5), -- the cache is syncing, it would be unwise to power down while this is occuring
    'raidSetFaulted',           # (6), --
    'highTemp',                 # (7), -- one or more sensors has exceeded the sensor's warning temp
    'raidSetLostblkEntry',      # (8), -- the raid set has lost blocks; see the Group Admin manual
    'secondaryEjectSWOpen',     # (9), -- the eject switch on the secondary controller has been opened; Please close it..
    'b2bFailure',               # (10), -- board to board communication between the active and secondary CMs has failed.. Call support?
    'replicationNoProg',        # (11), -- no progress in replicating a volume. Check network connectivity between partners.
    'raidSpareTooSmall',        # (12), -- a drive considered a spare is too small to use
    'lowTemp',                  # (13), -- one or more sensors is below the sensor's warning temp range
    'powerSupplyFailed',        # (14), -- one of the power supplies failed
    'timeOfDayClkBatteryLow',   # (15), -- time of day clock battery is low
    'incorrectPhysRamSize',     # (16), -- incorrect physical ram size
    'mixedMedia',               # (17), -- drive incompatibilities present
    'sumoChannelCardMissing',   # (18), -- sumo channel card missing
    'sumoChannelCardFailed',    # (19), -- sumo channel card failed
    'batteryLessthan72hours',   # (20), -- The battery has insufficient charge to survive a 72 hour power outage.
    'cpuFanNotSpinning',        # (21), -- The CPU fan is not functioning properly
    'raidMoreSparesExpected',   # (22), -- more spares are expected
    'raidSpareWrongType',       # (23), -- a spare if the wrong type of spare
    'raidSsdRaidsetHasHdd',     # (24), -- SSD RAIDset has a HDD
    'driveNotApproved',         # (25), -- one or more drives is not approved
    'noEthernetFlowControl',    # (26), -- Ethernet flow control disabled
    'fanRemovedCondition',      # (27),
    'smartBatteryLowCharge',    # (28),
    'nandHighBadBlockCount',    # (29), -- NAND chip on control module is reporting a large number of bad blocks.
    'networkStorm',             # (30), -- Array is experiencing a network storm
    'batteryEndOfLifeWarning',  # (31)
)
DELL_EQL_CRITICAL_CONDITIONS = (
    'raidSetDoubleFaulted',            # (0), -- the raid set is double faulted; the psg wont come up without user intervention; See the admin guide
    'bothFanTraysRemoved',             # (1), -- both fan trays are removed; How are you even seeing this message?
    'highAmbientTemp',                 # (2), -- one or more sensors has exceeded its critical temperature tthreshold
    'raidLostCache',                   # (3), -- The RAID driver is unable to recover the battery-backed cache.  The disk array will not initialize without user intervention.  See the Handling Lost Data section in the Group Administration manual for more information.
    'moreThanOneFanSpeedCondition',    # (4), -- more than one fan is operating outside its normal parameters
    'fanTrayRemoved',                  # (5), -- a fan tray has been removed. Loss of the other fan tray will result in the PSA overheating
    'raidSetLostblkTableFull',         # (6), -- the raid lost block table is full; what is the user supposed to do about this? see the admin guide?
    'raidDeviceIncompatible',          # (7), -- RAID Device is incompatible with platform.
    'raidOrphanCache',                 # (8), -- The RAID driver has found data in the battery-backed cache with no matching disk array.  Initialization will not proceed without user intervention. Call EqualLogic Support for assistance.
    'raidMultipleRaidSets',            # (9), -- Multiple valid RAIDsets were found.  The array cannot choose which one to initialize.  Remove all but one valid RAIDset and power-cycle the array.
    'nVRAMBatteryFailed',              # (10), -- The NVRAM battery has failed. The NVRAM can no longer be used.
    'hwComponentFailedCrit',           # (11), -- A critical hardware component has failed
    'incompatControlModule',           # (12), -- An incorrect control module has been inserted into the chassis
    'lowAmbientTemp',                  # (13), -- one or more sensors is below its critical temperature range
    'opsPanelFailure',                 # (14), -- Ops Panel is missing or broken
    'emmLinkFailure',                  # (15), -- Enclosure management services are unavailable
    'highBatteryTemperature',          # (16), -- Cache battery temperature exceeds upper limit; battery charger is disabled.
    'enclosureOpenPerm',               # (17), -- Enclosure open for a long time
    'sumoChannelBothMissing',          # (18), -- Both Sumo Channel cards missing
    'sumoEIPFailureCOndition',         # (19), -- EIP failed in Sumo.
    'sumoChannelBothFailed',           # (20), -- Both Sumo Channel cards failed
    'staleMirrorDiskFailure',          # (21), -- Stale mirror disk failure
    'c2fPowerModuleFailureCondition',  # (22), -- Cache to flash power module failed
    'raidsedUnresolved',               # (23), -- Raid sed is unresolved.
    'colossusDeniedFullPower',         # (24), -- Colossus was denied full power. Drive I/O is unavailable.
    'cemiUpdateInProgress',            # (25), -- CEMI update is in progress.
    'colossusCannotStart',             # (26), -- Colossus cannot start normal operation.
    'multipleFansRemoved',             # (27), -- Multiple fans removed
    'smartBatteryFailure',             # (28), -- Smart Battery failure
    'critbit29',                       # (29), -- available
    'nandFailure',                     # (30), -- NAND chip on control module failed to restore persistent data.
    'batteryEndOfLife',                # (31)

)


def byte_to_index(bytelist):
    bitindex = reduce(lambda a, b: (a << 8) + b, bytelist)
    if bitindex == 0:
        return []
    return filter(lambda i: 1 << (31 - i) & bitindex, range(32))


def parse_dell_eql_member(string_table):
    parsed = []

    for name, desc, health, warnings, critical, raid, storage, repl, snap, used in string_table:
        parsed.append(
            EqlMember(
                name=name,
                desc=desc,
                health=State((int(health) - 1) % 4),
                warnings=[DELL_EQL_WARNING_CONDITIONS[idx] for idx in byte_to_index(warnings[:4])],
                critical=[DELL_EQL_CRITICAL_CONDITIONS[idx] for idx in byte_to_index(critical[:4])],
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

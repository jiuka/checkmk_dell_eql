# Checkmk extension for Dell EqualLogic Storage Systems

![build](https://github.com/jiuka/checkmk_phion/workflows/build/badge.svg)
![flake8](https://github.com/jiuka/checkmk_phion/workflows/Lint/badge.svg)
![pytest](https://github.com/jiuka/checkmk_phion/workflows/pytest/badge.svg)

## Description

> :warning: I do **NOT** have access to the hardware to test this any more.

### dell_qel_disk
Monitors disk health and throughput per disk or summarized per device.

### dell_eql_fan
Monitors fan health and speed.

### dell_qel_member
Replaces the `dell_eql_storage` check and outputs why the storage device is in a unhealthy state.

### dell_qel_temp
Monitors temperature sensor state and readings.

### dell_qel_volume
Monitors state access type and iops, throughput and latency.

## Development

For the best development experience use [VSCode](https://code.visualstudio.com/) with the [Remote Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension. This maps your workspace into a checkmk docker container giving you access to the python environment and libraries the installed extension has.

## Directories

The following directories in this repo are getting mapped into the Checkmk site.

* `agents`, `checkman`, `checks`, `doc`, `inventory`, `notifications`, `pnp-templates`, `web` are mapped into `local/share/check_mk/`
* `agent_based` is mapped to `local/lib/check_mk/base/plugins/agent_based`
* `nagios_plugins` is mapped to `local/lib/nagios/plugins`

## Continuous integration
### Local

To build the package hit `Crtl`+`Shift`+`B` to execute the build task in VSCode.

`pytest` can be executed from the terminal or the test ui.

### Github Workflow

The provided Github Workflows run `pytest` and `flake8` in the same checkmk docker conatiner as vscode.

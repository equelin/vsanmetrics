# vsanmetrics

vsanmetrics is a tool written in Python for collecting usage and performance metrics from a VMware vSAN cluster and translating them in [InfluxDB's line protocol](https://github.com/influxdata/telegraf/blob/master/docs/DATA_FORMATS_INPUT.md).

It can be useful to send metrics in a [InfluxDB](https://www.influxdata.com/) database with the help of [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/) and then display metrics in [Grafana](https://grafana.com/).

## Prerequisites

- Python (This script has been tested with python 2.7.12)
- [Pyvmomi](https://github.com/vmware/pyvmomi#installing)

> You can install pyvmomi with pip -> `pip install pyvmomi`

- [VMware vSAN Management SDK for python](https://code.vmware.com/web/sdk/6.7.0/vsan-python)

> To use the vSAN Python bindings, download the SDK and place `vsanmgmtObjects.py` and `vsanapiutis.py` on a path where your Python applications can import library or in the same folder than `vsanmetrics.py`.

## Installation

- Download the script `vsanmetrics.py`
- On linux box, make the script executable

```bash
% chmod +x ./vsanmetrics
```

- Run the script with the -h parameter to check if it works

```bash
% ./vsanmetrics -h

usage: vsanmetrics.py [-h] -s VCENTER [-o PORT] -u USER [-p PASSWORD] -c CLUSTERNAME

Get vSAN cluster statistics

optional arguments:
  -h, --help            show this help message and exit
  -s VCENTER, --vcenter VCENTER
                        Remote vcenter to connect to
  -o PORT, --port PORT  Port to connect on
  -u USER, --user USER  User name to use when connecting to vcenter
  -p PASSWORD, --password PASSWORD
                        Password to use when connecting to vcenter
  -c CLUSTERNAME, --cluster_name CLUSTERNAME
                        Cluster Name
```

- Run the script against a vSAN cluster. It should output some metrics like in this example

```bash
./vsanmetrics.py -s vcenter.example.com -u administrator@vsphere.local -p MyAwesomePassword -c VSAN-CLUSTER

capacity_global,scope=global,vcenter=vcenter.example.com,cluster=VSAN-CLUSTER totalCapacityB=7200999211008,freeCapacityB=1683354550260 1525422314084382976
capacity_summary,scope=summary,vcenter=vcenter.example.com,cluster=VSAN-CLUSTER temporaryOverheadB=0,physicalUsedB=2636212338688,primaryCapacityB=2688980877312,usedB=5380734189568,reservedCapacityB=3607749040540,overReservedB=2744521850880,provisionCapacityB=6986210377728,overheadB=2828663783436 1525422314084382976
capacity_vmswap,scope=vmswap,vcenter=vcenter.example.com,cluster=VSAN-CLUSTER temporaryOverheadB=0,physicalUsedB=8422162432,primaryCapacityB=177330978816,usedB=355240771584,reservedCapacityB=355089776640,overReservedB=346818609152,overheadB=177909792768 1525422314084382976
capacity_checksumOverhead,scope=checksumOverhead,vcenter=vcenter.example.com,cluster=VSAN-CLUSTER temporaryOverheadB=0,physicalUsedB=0,primaryCapacityB=0,usedB=8858370048,reservedCapacityB=0,overReservedB=0,overheadB=8858370048 1525422314084382976
```

## Using vsanmetrics with Telegraf

The `exec` input plugin of Telegraf executes the `commands` on every interval and parses metrics from their output in any one of the accepted [Input Data Formats](https://github.com/influxdata/telegraf/blob/master/docs/DATA_FORMATS_INPUT.md).

> Don't forget to configure Telegraf to output data to InfluxDB !

`vsanmetrics` output the metrics in InfluxDB's line protocol. Telegraf will parse them and send them to the InfluxDB database.

`vsanmetrics` and `pyvmomi` should be available by the user who run the Telegraf service. (typically root on Linux boxes...).

> TIP: On Linux, install pyvmomi with the command `sudo -H pip install pyvmomi` to make it available to the root user. 

Here is an example of a working telegraf's config file:

```Toml
###############################################################################
#                            INPUT PLUGINS                                    #
###############################################################################

[[inputs.exec]]
  # Shell/commands array
  # Full command line to executable with parameters, or a glob pattern to run all matching files.
  commands = ["/path/to/script/vsanmetrics.py -s vcenter01.example.com -u administrator@vsphere.local -p MyAwesomePassword -c VSAN-CLUSTER"]

  # Timeout for each command to complete.
  timeout = "60s"

  # Data format to consume.
  # NOTE json only reads numerical measurements, strings and booleans are ignored.
  data_format = "influx"

  interval = "300s"
```

If needed, you can specify more than one input plugin. It might be useful if you want to gather different statistics with different intervals or if you want to query different vSAN clusters.

```Toml
###############################################################################
#                            INPUT PLUGINS                                    #
###############################################################################

[[inputs.exec]]
  # Shell/commands array
  # Full command line to executable with parameters, or a glob pattern to run all matching files.
  commands = ["/path/to/script/vsanmetrics.py -s vcenter01.example.com -u administrator@vsphere.local -p MyAwesomePassword -c VSAN-CLUSTER"]

  # Timeout for each command to complete.
  timeout = "60s"

  # Data format to consume.
  # NOTE json only reads numerical measurements, strings and booleans are ignored.
  data_format = "influx"

  interval = "300s"

[[inputs.exec]]
  # Shell/commands array
  # Full command line to executable with parameters, or a glob pattern to run all matching files.
  commands = ["/path/to/script/vsanmetrics.py -s vcenter02.example.com -u administrator@vsphere.local -p MyAwesomePassword -c VSAN-CLUSTER"]

  # Timeout for each command to complete.
  timeout = "60s"

  # Data format to consume.
  # NOTE json only reads numerical measurements, strings and booleans are ignored.
  data_format = "influx"

  interval = "300s"
```

# Author
**Erwan Quélin**
- <https://github.com/equelin>
- <https://twitter.com/erwanquelin>

# License

Copyright 2018 Erwan Quelin and the community.

Licensed under the Apache License 2.0.
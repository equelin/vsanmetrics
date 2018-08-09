# vsanmetrics

vsanmetrics is a tool written in Python for collecting usage and performance metrics and health status from a VMware vSAN cluster and translating them in [InfluxDB's line protocol](https://github.com/influxdata/telegraf/blob/master/docs/DATA_FORMATS_INPUT.md).

It can be useful to send metrics in a time-serie database like [InfluxDB](https://www.influxdata.com/) or [Graphite](https://graphiteapp.org/) with the help of [Telegraf](https://www.influxdata.com/time-series-platform/telegraf/) and then display metrics in [Grafana](https://grafana.com/).

A detailed list of all entities types and metrics is available [here](entities.md)

## Prerequisites

- Python (This script has been tested with python 2.7.12)
- [Pyvmomi](https://github.com/vmware/pyvmomi#installing) python's librairy

> You can install the librairies with pip -> `pip install -r requirements.txt`

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

usage: vsanmetrics.py [-h] -s VCENTER [-o PORT] -u USER [-p PASSWORD] -c
                      CLUSTERNAME [--performance] [--capacity] [--health]
                      [--skipentitytypes SKIPENTITYTYPES]

Export vSAN cluster performance and storage usage statistics to InfluxDB line
protocol

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
  --performance         Output performance metrics
  --capacity            Output storage usage metrics
  --health              Output cluster health status
  --skipentitytypes SKIPENTITYTYPES
                        List of entity types to skip. Separated by a comma
```

## Usage

Run the script against a vSAN cluster to gather the storage usage statistics.

```bash
% ./vsanmetrics.py -s vcenter.example.com -u administrator@vsphere.local -p MyAwesomePassword -c VSAN-CLUSTER --capacity

capacity_global,scope=global,vcenter=vcenter.example.com,cluster=VSAN-CLUSTER totalCapacityB=7200999211008,freeCapacityB=1683354550260 1525422314084382976
capacity_summary,scope=summary,vcenter=vcenter.example.com,cluster=VSAN-CLUSTER temporaryOverheadB=0,physicalUsedB=2636212338688,primaryCapacityB=2688980877312,usedB=5380734189568,reservedCapacityB=3607749040540,overReservedB=2744521850880,provisionCapacityB=6986210377728,overheadB=2828663783436 1525422314084382976
capacity_vmswap,scope=vmswap,vcenter=vcenter.example.com,cluster=VSAN-CLUSTER temporaryOverheadB=0,physicalUsedB=8422162432,primaryCapacityB=177330978816,usedB=355240771584,reservedCapacityB=355089776640,overReservedB=346818609152,overheadB=177909792768 1525422314084382976
capacity_checksumOverhead,scope=checksumOverhead,vcenter=vcenter.example.com,cluster=VSAN-CLUSTER temporaryOverheadB=0,physicalUsedB=0,primaryCapacityB=0,usedB=8858370048,reservedCapacityB=0,overReservedB=0,overheadB=8858370048 1525422314084382976
```

Run the script against a vSAN cluster to gather performance statistics.

```bash
% ./vsanmetrics.py -s vcenter.example.com -u administrator@vsphere.local -p MyAwesomePassword -c VSAN-CLUSTER --performance

cluster-domclient,cluster=VSAN-CLUSTER,vcenter=vcenter.example.com,uuid=52b29fa6-9cb9-6d67-31ed-4bf8f2dd9294 oio=7.0,throughputRead=40883.0,latencyAvgWrite=11218.0,latencyAvgRead=985.0,iopsRead=1.0,throughputWrite=2819.0,congestion=0.0,iopsWrite=0.0 1525462200000000000
cluster-domcompmgr,cluster=VSAN-CLUSTER,vcenter=vcenter.example.com,uuid=52b29fa6-9cb9-6d67-31ed-4bf8f2dd9294 oio=6.0,throughputRecWrite=0.0,latencyAvgRecWrite=0.0,throughputRead=45309.0,latencyAvgWrite=1335.0,tputResyncRead=0.0,latencyAvgRead=935.0,iopsRead=1.0,throughputWrite=14476.0,latAvgResyncRead=0.0,iopsResyncRead=0.0,iopsRecWrite=0.0,iopsWrite=2.0,congestion=0.0 1525462200000000000
host-domclient,cluster=VSAN-CLUSTER,vcenter=vcenter.example.com,hostname=esx01.example.com,uuid=5ae60a2b-fe13-25dd-1f19-005056a3a442 oio=1.0,throughputRead=95.0,latencyAvgWrite=0.0,latencyAvgRead=340.0,iopsRead=0.0,clientCacheHitRate=0.0,throughputWrite=0.0,congestion=0.0,iopsWrite=0.0,clientCacheHits=0.0 1525462200000000000
host-domclient,cluster=VSAN-CLUSTER,vcenter=vcenter.example.com,hostname=esx03.example.com,uuid=5ae750e2-bc6d-487b-1283-005056a38be2 oio=6.0,throughputRead=40788.0,latencyAvgWrite=11218.0,latencyAvgRead=1000.0,iopsRead=1.0,clientCacheHitRate=0.0,throughputWrite=2819.0,congestion=0.0,iopsWrite=0.0,clientCacheHits=0.0 1525462200000000000
host-domclient,cluster=VSAN-CLUSTER,vcenter=vcenter.example.com,hostname=esx02.example.com,uuid=5ae7229f-771d-1091-ffe7-005056a35f01 oio=0.0,throughputRead=0.0,latencyAvgWrite=0.0,latencyAvgRead=0.0,iopsRead=0.0,clientCacheHitRate=0.0,throughputWrite=0.0,congestion=0.0,iopsWrite=0.0,clientCacheHits=0.0 1525462200000000000
```

Run the script against a vSAN cluster to gather performance statistics and skip some entity types like virtual machines or VSCSI entities:

```bash
% ./vsanmetrics.py -s vcenter.example.com -u administrator@vsphere.local -p MyAwesomePassword -c VSAN-CLUSTER --performance --skipentitytypes virtual-machine,vscsi

cluster-domclient,cluster=VSAN-CLUSTER,vcenter=vcenter.example.com,uuid=52b29fa6-9cb9-6d67-31ed-4bf8f2dd9294 oio=7.0,throughputRead=40883.0,latencyAvgWrite=11218.0,latencyAvgRead=985.0,iopsRead=1.0,throughputWrite=2819.0,congestion=0.0,iopsWrite=0.0 1525462200000000000
cluster-domcompmgr,cluster=VSAN-CLUSTER,vcenter=vcenter.example.com,uuid=52b29fa6-9cb9-6d67-31ed-4bf8f2dd9294 oio=6.0,throughputRecWrite=0.0,latencyAvgRecWrite=0.0,throughputRead=45309.0,latencyAvgWrite=1335.0,tputResyncRead=0.0,latencyAvgRead=935.0,iopsRead=1.0,throughputWrite=14476.0,latAvgResyncRead=0.0,iopsResyncRead=0.0,iopsRecWrite=0.0,iopsWrite=2.0,congestion=0.0 1525462200000000000
host-domclient,cluster=VSAN-CLUSTER,vcenter=vcenter.example.com,hostname=esx01.example.com,uuid=5ae60a2b-fe13-25dd-1f19-005056a3a442 oio=1.0,throughputRead=95.0,latencyAvgWrite=0.0,latencyAvgRead=340.0,iopsRead=0.0,clientCacheHitRate=0.0,throughputWrite=0.0,congestion=0.0,iopsWrite=0.0,clientCacheHits=0.0 1525462200000000000
host-domclient,cluster=VSAN-CLUSTER,vcenter=vcenter.example.com,hostname=esx03.example.com,uuid=5ae750e2-bc6d-487b-1283-005056a38be2 oio=6.0,throughputRead=40788.0,latencyAvgWrite=11218.0,latencyAvgRead=1000.0,iopsRead=1.0,clientCacheHitRate=0.0,throughputWrite=2819.0,congestion=0.0,iopsWrite=0.0,clientCacheHits=0.0 1525462200000000000
host-domclient,cluster=VSAN-CLUSTER,vcenter=vcenter.example.com,hostname=esx02.example.com,uuid=5ae7229f-771d-1091-ffe7-005056a35f01 oio=0.0,throughputRead=0.0,latencyAvgWrite=0.0,latencyAvgRead=0.0,iopsRead=0.0,clientCacheHitRate=0.0,throughputWrite=0.0,congestion=0.0,iopsWrite=0.0,clientCacheHits=0.0 1525462200000000000
```

## List of available entities types

A more detailed list of entities and metrics is available [here](entities.md)

|Name|Description|
|---|---|
|cluster-domclient|Metrics about clusters in the perspective of VM consumption.|
|cluster-domcompmgr|Metrics about clusters in the perspective of vSAN backend.|
|host-domclient|Metrics about hosts in the perspective of VM consumption|
|host-domcompmgr|Metrics about hosts in the perspective of vSAN backend.|
|cache-disk|Metrics about Cache-tier disks|
|capacity-disk|Metrics about Capacity-tier disks|
|disk-group|Metrics about disk groups.|
|vscsi|Metrics for Virtual SCSI of virtual machines|
|virtual-machine|Metrics for virtual machines|
|virtual-disk|Metrics for virtual disks.|
|vsan-vnic-net|Metrics for vSAN VMkernel Network Adapter.|
|vsan-host-net|Metrics for vSAN Host Network.|
|vsan-pnic-net|Metrics for vSAN physical NIC.|
|vsan-iscsi-host|Metrics for all vSAN iSCSI targets on this ESXi host.|
|vsan-iscsi-target|Metrics for all LUNs on a vSAN iSCSI target.|
|vsan-iscsi-lun|Metrics for a vSAN iSCSI LUN.|

## Using vsanmetrics with Telegraf

The `exec` input plugin of Telegraf executes the `commands` on every interval and parses metrics from their output in any one of the accepted [Input Data Formats](https://github.com/influxdata/telegraf/blob/master/docs/DATA_FORMATS_INPUT.md).

> Don't forget to configure Telegraf to output data to a [time series database](https://docs.influxdata.com/telegraf/v1.6/concepts/data_formats_output/) !

`vsanmetrics` output the metrics in InfluxDB's line protocol. Telegraf will parse them and send them to any data format configured in the [outputs plugins](https://docs.influxdata.com/telegraf/v1.6/plugins/outputs/).

`vsanmetrics` and and the Python's librairies should be available by the user who run the Telegraf service. (typically root on Linux boxes...).

> TIP: On Linux, install the librairies with the command `sudo -H pip install -r requirements.txt` to make it available to the root user.

Here is an example of a working telegraf's config file:

```Toml
###############################################################################
#                            INPUT PLUGINS                                    #
###############################################################################

[[inputs.exec]]
  # Shell/commands array
  # Full command line to executable with parameters, or a glob pattern to run all matching files.
  commands = ["/path/to/script/vsanmetrics.py -s vcenter01.example.com -u administrator@vsphere.local -p MyAwesomePassword -c VSAN-CLUSTER --performance --capacity --health"]

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
  commands = ["/path/to/script/vsanmetrics.py -s vcenter01.example.com -u administrator@vsphere.local -p MyAwesomePassword -c VSAN-CLUSTER --performance --capacity --health"]

  # Timeout for each command to complete.
  timeout = "60s"

  # Data format to consume.
  # NOTE json only reads numerical measurements, strings and booleans are ignored.
  data_format = "influx"

  interval = "300s"

[[inputs.exec]]
  # Shell/commands array
  # Full command line to executable with parameters, or a glob pattern to run all matching files.
  commands = ["/path/to/script/vsanmetrics.py -s vcenter02.example.com -u administrator@vsphere.local -p MyAwesomePassword -c VSAN-CLUSTER --performance --capacity --health"]

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

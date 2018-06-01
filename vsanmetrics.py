#!/usr/bin/env python

# Erwan Quelin - erwan.quelin@gmail.com

from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import pbm, VmomiSupport, SoapStubAdapter, vim, vmodl

import argparse
import atexit
import getpass
from datetime import datetime, timedelta
import time
import ssl

import vsanapiutils
import vsanmgmtObjects


def get_args():  
    parser = argparse.ArgumentParser(
        description='Export vSAN cluster performance and storage usage statistics to InfluxDB line protocol')

    parser.add_argument('-s', '--vcenter',
                        required=True,
                        action='store',
                        help='Remote vcenter to connect to')

    parser.add_argument('-o', '--port',
                        type=int,
                        default=443,
                        action='store',
                        help='Port to connect on')

    parser.add_argument('-u', '--user',
                        required=True,
                        action='store',
                        help='User name to use when connecting to vcenter')

    parser.add_argument('-p', '--password',
                        required=False,
                        action='store',
                        help='Password to use when connecting to vcenter')

    parser.add_argument('-c', '--cluster_name', 
                        dest='clusterName', 
                        required=True,
                        help='Cluster Name')

    parser.add_argument("--performance",
                        help="Output performance metrics",
                        action="store_true")

    parser.add_argument("--capacity",
                        help="Output storage usage metrics",
                        action="store_true")

    parser.add_argument('--skipentitytypes',
                    required=False,
                    action='store',
                    help='List of entity types to skip. Separated by a comma')

    args = parser.parse_args()

    if not args.password:
        args.password = getpass.getpass(
            prompt='Enter password for host %s and user %s: ' %
                   (args.vcenter, args.user))

    if not args.performance and args.skipentitytypes:
        print("You can't skip a performance entity type if you don't provide the --performance tag")
        exit()

    if not args.performance and not args.capacity:
        print('Please provide tag(s) --performance and/or --capacity to specify what type of data you want to collect')
        exit()

    return args

# Get cluster informations
def getClusterInstance(clusterName, content):
   searchIndex = content.searchIndex
   datacenters = content.rootFolder.childEntity
   for datacenter in datacenters:
      cluster = searchIndex.FindChild(datacenter.hostFolder, clusterName)
      if cluster is not None:
         return cluster
   return None

def getInformations(witnessHosts, cluster):

    uuid = {}
    hostnames = {}
    disks = {}

    ### Get Host and disks informations
    for host in cluster.host:

        #Get relationship between host id and hostname 
        hostnames[host.summary.host] = host.summary.config.name

        #Get all disk (cache and capcity) attached to hosts in the cluster
        diskAll = host.configManager.vsanSystem.QueryDisksForVsan()

        for disk in diskAll:
            if disk.state == 'inUse':
                uuid[disk.vsanUuid] = disk.disk.canonicalName
                disks[disk.vsanUuid] = host.summary.config.name

    for vsanHostConfig in cluster.configurationEx.vsanHostConfig:
        uuid[vsanHostConfig.clusterInfo.nodeUuid] = hostnames[vsanHostConfig.hostSystem]

    ### Get witness disks informations



    return uuid , disks

# Get hosts informations (hostname and disks)
def getHostsInfos(cluster):
    disksinfos = {}
    hostnames = {}
    hostinfos = {}

    for host in cluster.host:
        hostnames[host.summary.host] = host.summary.config.name

        diskAll = host.configManager.vsanSystem.QueryDisksForVsan()

        for disk in diskAll:
            if disk.state == 'inUse':
                disksinfos[disk.vsanUuid] = disk.disk.canonicalName

    for vsanHostConfig in cluster.configurationEx.vsanHostConfig:
        hostinfos[vsanHostConfig.clusterInfo.nodeUuid] = hostnames[vsanHostConfig.hostSystem]

    return disksinfos,hostinfos

# Get all VM managed by vCenter, return array with name and uuid of the VMs
def getVMs(content):
    container = content.rootFolder  # starting point to look into
    viewType = [vim.VirtualMachine]  # object types to look for
    recursive = True  # whether we should look into it recursively
    containerView = content.viewManager.CreateContainerView(container, viewType, recursive)

    children = containerView.view

    vms = {}

    for child in children:
        vms[child.summary.config.instanceUuid] = child.summary.config.name

    return vms

# OUtput data in the Influx Line protocol format
def printInfluxLineProtocol(measurement,tags,fields,timestamp):
    result = "%s,%s %s %i" % (measurement,arrayToString(tags),arrayToString(fields),timestamp)
    print(result)

# Convert time in string format to epoch timestamp (nanosecond)
def convertStrToTimestamp(str):
    sec = time.mktime(datetime.strptime(str, "%Y-%m-%d %H:%M:%S").timetuple())

    ns = int(sec * 1000000000)

    return ns

# parse EntytyRefID, convert to tags
def parseEntityRefId(measurement,entityRefId,uuid,vms,disks):

    tags = {}

    if measurement == 'vscsi':
        entityRefId = entityRefId.split("|")
        split = entityRefId[0].split(":")

        tags['uuid'] = split[1]
        tags['vscsi'] = entityRefId[1]
        tags['vmname'] = vms[split[1]]
    else:
        entityRefId = entityRefId.split(":")

        if measurement == 'cluster-domclient':
            tags['uuid'] = entityRefId[1]

        if measurement == 'cluster-domcompmgr':
            tags['uuid'] = entityRefId[1]

        if measurement == 'host-domclient':
            tags['uuid'] = entityRefId[1]
            tags['hostname'] = uuid[entityRefId[1]] 

        if measurement == 'host-domcompmgr':
            tags['uuid'] = entityRefId[1]
            tags['hostname'] = uuid[entityRefId[1]] 

        if measurement == 'cache-disk':
            tags['uuid'] = entityRefId[1]
            tags['naa'] = uuid[entityRefId[1]]
            tags['hostname'] = disks[entityRefId[1]]

        if measurement == 'capacity-disk':
            tags['uuid'] = entityRefId[1]
            tags['naa'] = uuid[entityRefId[1]]
            tags['hostname'] = disks[entityRefId[1]]

        if measurement == 'disk-group':
            tags['uuid'] = entityRefId[1]

        if measurement == 'virtual-machine':
            tags['uuid'] = entityRefId[1]
            tags['vmname'] = vms[entityRefId[1]]

        if measurement == 'virtual-disk':
            split = entityRefId[1].split("/")     

            tags['uuid'] = split[0]
            tags['disk'] = split[1]

        if measurement == 'vsan-vnic-net':
            split = entityRefId[1].split("|")     

            tags['uuid'] = split[0]
            tags['hostname'] = uuid[split[0]] 
            tags['stack'] = split[1]
            tags['vmk'] = split[2]

        if measurement == 'vsan-host-net':
            tags['uuid'] = entityRefId[1]
            tags['hostname'] = uuid[entityRefId[1]] 

        if measurement == 'vsan-pnic-net':

            split = entityRefId[1].split("|")     

            tags['uuid'] = split[0]
            tags['hostname'] = uuid[split[0]] 
            tags['vmnic'] = split[1]

        if measurement == 'vsan-iscsi-host':
            tags['uuid'] = entityRefId[1]
            tags['hostname'] = uuid[entityRefId[1]] 

        if measurement == 'vsan-iscsi-target':
            tags['uuid'] = entityRefId[1]
            tags['hostname'] = uuid[entityRefId[1]] 

        if measurement == 'vsan-iscsi-lun':
            tags['uuid'] = entityRefId[1]
            tags['hostname'] = uuid[entityRefId[1]] 

    return tags

# Convert array to a string compatible with influxdb line protocol tags or fields
def arrayToString(data):
    i = 0
    result = ""

    for key,val in data.items():
        if i == 0:
            result = "%s=%s" % (key,val)
        else:
            result = result + ",%s=%s" % (key,val)
        i = i + 1 
    return result

def parseVsanObjectSpaceSummary(data):
    fields = {}

    fields['overheadB'] = data.overheadB
    fields['overReservedB'] = data.overReservedB
    fields['physicalUsedB'] = data.physicalUsedB
    fields['primaryCapacityB'] = data.primaryCapacityB
    fields['reservedCapacityB'] = data.reservedCapacityB
    fields['temporaryOverheadB'] = data.temporaryOverheadB
    fields['usedB'] = data.usedB
    
    if data.provisionCapacityB:
        fields['provisionCapacityB'] = data.provisionCapacityB
    
    return fields

def parseVimVsanDataEfficiencyCapacityState(data):
    fields = {}

    fields['dedupMetadataSize'] = data.dedupMetadataSize
    fields['logicalCapacity'] = data.logicalCapacity
    fields['logicalCapacityUsed'] = data.logicalCapacityUsed
    fields['physicalCapacity'] = data.physicalCapacity
    fields['physicalCapacityUsed'] = data.physicalCapacityUsed
    fields['ratio'] = float(data.logicalCapacityUsed) / float(data.physicalCapacityUsed)

    return fields    

def parseCapacity(scope,data,tagsbase,timestamp):

    tags = {}
    fields = {}

    tags['scope'] = scope
    tags.update(tagsbase)
    measurement = 'capacity_' + scope

    if scope == 'global':
        fields['freeCapacityB'] = data.freeCapacityB
        fields['totalCapacityB'] = data.totalCapacityB

    elif scope == 'summary':
        fields = parseVsanObjectSpaceSummary(data.spaceOverview)

    elif scope == 'efficientcapacity':
        fields = parseVimVsanDataEfficiencyCapacityState(data.efficientCapacity)
    else:
        fields = parseVsanObjectSpaceSummary(data)

    printInfluxLineProtocol(measurement,tags,fields,timestamp)

# Main...
def main():

    # Don't check for valid certificate
    context = ssl._create_unverified_context()

    # Parse CLI arguments
    args = get_args()

    # Connect to vCenter
    try:
        si = SmartConnect(host=args.vcenter,
                                                user=args.user,
                                                pwd=args.password,
                                                port=int(args.port),
                                                sslContext=context)
        if not si:
            print("Could not connect to the specified host using specified "
                  "username and password")

            return -1
    except vmodl.MethodFault as e:
        print("Caught vmodl fault : " + e.msg)
        return -1

    except Exception as e:
        print("Caught exception : " + str(e))
        return -1

    # Disconnect to vcenter at the end
    atexit.register(Disconnect, si)

    # Get content informations
    content = si.RetrieveContent()

    # Get Info about cluster
    cluster_obj = getClusterInstance(args.clusterName,content)
    
    # Exit if the cluster provided in the arguments is not available
    if not cluster_obj:
        print 'The required cluster not found in inventory, validate input.'
        exit()

    # Initiate tags with vcenter and cluster name
    tagsbase = {}
    tagsbase['vcenter'] = args.vcenter
    tagsbase['cluster'] = args.clusterName

    apiVersion = vsanapiutils.GetLatestVmodlVersion(args.vcenter)
    vcMos = vsanapiutils.GetVsanVcMos(si._stub, context=context, version=apiVersion)

    ## CAPACITY

    if args.capacity:
        vsanSpaceReportSystem = vcMos['vsan-cluster-space-report-system']

        try:
            spaceReport = vsanSpaceReportSystem.VsanQuerySpaceUsage(
                cluster = cluster_obj
                )
        except vmodl.fault.InvalidArgument as e:
            print("Caught InvalidArgument exception : " + str(e))
            return -1    
        except vmodl.fault.NotSupported as e:
            print("Caught NotSupported exception : " + str(e))
            return -1

        except vmodl.fault.RuntimeFault as e:
            print("Caught RuntimeFault exception : " + str(e))
            return -1

        timestamp = int(time.time() * 1000000000)

        parseCapacity('global',spaceReport,tagsbase,timestamp)
        parseCapacity('summary',spaceReport,tagsbase,timestamp)

        if spaceReport.efficientCapacity:
            parseCapacity('efficientcapacity',spaceReport,tagsbase,timestamp)

        for object in spaceReport.spaceDetail.spaceUsageByObjectType:
            parseCapacity(object.objType,object,tagsbase,timestamp)

    ## PERFORMANCE
    if args.performance:

        vsanVcStretchedClusterSystem = vcMos['vsan-stretched-cluster-system']
        vsanPerfSystem =  vcMos['vsan-performance-manager']

        # Get VM uuid/names
        vms = getVMs(content)

        # Get uuid/names relationship informations for hosts and disks
        uuid, disks = getInformations(content, cluster_obj)

        #### Witness
        # Retrieve Witness Host for given VSAN Cluster
        witnessHosts = vsanVcStretchedClusterSystem.VSANVcGetWitnessHosts(
            cluster=cluster_obj
            )

        for witnessHost in witnessHosts:
            host = (vim.HostSystem(witnessHost.host._moId,si._stub))

            uuid[witnessHost.nodeUuid] = host.name

            diskWitness = host.configManager.vsanSystem.QueryDisksForVsan()

            for disk in diskWitness:
                if disk.state == 'inUse':
                    uuid[disk.vsanUuid] = disk.disk.canonicalName


        # Gather a list of the available entity types (ex: vsan-host-net)
        entityTypes = vsanPerfSystem.VsanPerfGetSupportedEntityTypes()

        # query interval, last 10 minutes -- UTC !!! 
        endTime = datetime.utcnow()
        startTime = endTime + timedelta(minutes=-10)

        splitSkipentitytypes = []

        if args.skipentitytypes:
                splitSkipentitytypes = args.skipentitytypes.split(',')

        for entities in entityTypes:

            if entities.name not in splitSkipentitytypes:
                   
                entitieName = entities.name

                labels = []

                # Gather all labels related to the entity (ex: iopsread, iopswrite...)
                for entity in entities.graphs:

                    for metric in entity.metrics:

                            labels.append(metric.label)

                # Build entity 
                entity = '%s:*' % (entities.name)

                # Build spec object
                spec = vim.cluster.VsanPerfQuerySpec(
                    endTime = endTime,
                    entityRefId = entity,
                    labels = labels,
                    startTime = startTime
                )

                # Get statistics
                try:
                    metrics = vsanPerfSystem.VsanPerfQueryPerf(
                        querySpecs = [spec],
                        cluster = cluster_obj
                    )

                except vmodl.fault.InvalidArgument as e:
                    print("Caught InvalidArgument exception : " + str(e))
                    return -1

                except vmodl.fault.NotFound as e:
                    print("Caught NotFound exception : " + str(e))
                    return -1

                except vmodl.fault.NotSupported as e:
                    print("Caught NotSupported exception : " + str(e))
                    return -1

                except vmodl.fault.RuntimeFault as e:
                    print("Caught RuntimeFault exception : " + str(e))
                    return -1

                except vmodl.fault.Timedout as e:
                    print("Caught Timedout exception : " + str(e))
                    return -1

                except vmodl.fault.VsanNodeNotMaster as e:
                    print("Caught VsanNodeNotMaster exception : " + str(e))
                    return -1

                for metric in metrics:

                    if not metric.sampleInfo == "":

                        measurement = entitieName    

                        sampleInfos = metric.sampleInfo.split(",")
                        lenValues = len(sampleInfos)

                        timestamp = convertStrToTimestamp(sampleInfos[lenValues - 1])

                        tags = parseEntityRefId(measurement,metric.entityRefId,uuid,vms,disks)

                        tags.update(tagsbase)

                        fields = {}

                        for value in metric.value:

                            listValue = value.values.split(",")

                            fields[value.metricId.label] = float(listValue[lenValues - 1])

                        printInfluxLineProtocol(measurement,tags,fields,timestamp) 

    return 0

# Start program
if __name__ == "__main__":
    main()

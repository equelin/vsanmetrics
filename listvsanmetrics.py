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
        description='Get vSAN cluster statistics')

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

    parser.add_argument('-f', '--format', 
                    dest='format',
                    default='markdown',
                    action='store',
                    required=True,
                    help='Output Format, markdown or HTML')

    args = parser.parse_args()
    if not args.password:
        args. password = getpass.getpass(
            prompt='Enter password for host %s and user %s: ' %
                   (args.vcenter, args.user))

    formatValues = ['markdown','html','raw']

    if (args.format).lower() not in formatValues:
        print("Format should be Markdown or HTML")
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
        print 'The required cluster not found in inventory, validate input. Aborting test'
        exit()

    apiVersion = vsanapiutils.GetLatestVmodlVersion(args.vcenter)
    vcMos = vsanapiutils.GetVsanVcMos(si._stub, context=context, version=apiVersion)

    vsanPerfSystem =  vcMos['vsan-performance-manager']

    # Gather a list of the available entity types (ex: vsan-host-net)
    entityTypes = vsanPerfSystem.VsanPerfGetSupportedEntityTypes()

    if (args.format).lower() == 'raw':
        print entityTypes

    if (args.format).lower() == 'markdown':

        print"## Entity types"
        print""
        print("|Name|Description|")
        print("|---|---|")

        for entities in entityTypes:
            print "|%s|%s|" % (entities.name,entities.description)

        print ""
        print"## Details"
        for entities in entityTypes:

            print ""
            print "### %s" % (entities.name)
            print ""
            print entities.description
            print ""
            print("|Label|Name|Unit|Description|")
            print("|---|---|---|---|")

            for entity in entities.graphs:

                unit = entity.unit

                for metric in entity.metrics:

                    print "|%s|%s|%s|%s|" % (metric.label,metric.name,unit,metric.description)
        print ""

    if (args.format).lower() == 'html':
        print("<table>")
        print("<thead><tr><th>Name</th><th>Description</th></tr></thead>")
        print("<tbody>")
        for entities in entityTypes:
            print "<tr><th>%s</th><th>%s</th></tr>" % (entities.name,entities.description)

        print("</tbody>")
        print("</table>")
        print ""
        for entities in entityTypes:

            print "<h3> %s </h3>" % (entities.name)
            print ""
            print entities.description
            print ""
            print("<table>")
            print("<thead><tr><th>Label</th><th>Name</th><th>Unit</th><th>Description</th></tr></thead>")
            print("<tbody>")

            for entity in entities.graphs:

                unit = entity.unit

                for metric in entity.metrics:

                    print "<tr><th>%s</th><th>%s</th><th>%s</th><th>%s</th></tr>" % (metric.label,metric.name,unit,metric.description)
            print("</tbody>")
            print("</table>")
            print ""

    return 0

# Start program
if __name__ == "__main__":
    main()

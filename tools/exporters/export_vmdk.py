# Copyright 2009-2013 Eucalyptus Systems, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
# Please contact Eucalyptus Systems, Inc., 6755 Hollister Ave., Goleta
# CA 93117, USA or visit http://www.eucalyptus.com/licenses/ if you need
# additional information or have any questions.


# Exports VMDK from vSphere into a folder
# Requires psphere that can be installed via 'pip install -U psphere'
# Exit codes
#     0 - OK
#     1 - server connection error
#     2 - invalid VM name
#     3 - no access to extend 
#     4 - not enough free disk space

import re
import urllib2
import base64
import sys
import os
import argparse
import logging
import getpass
import subprocess

# this helps to suppress Warning from psphere module about missed config file that we don't need
logging.basicConfig(level=logging.ERROR)

from suds import WebFault
from psphere.client import Client
from psphere.managedobjects import VirtualMachine
from psphere.managedobjects import Datacenter
from psphere.errors import ObjectNotFoundError

def downloadFile(uri, user, passwd, destination):
    request = urllib2.Request(uri)
    f = open(destination, 'wb')
    base64string = base64.encodestring('%s:%s' % (user, passwd)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    u = urllib2.urlopen(request)
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading %s bytes" % (file_size)
    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break
        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,
    f.close()
    print "File saved to %s" % (destination)

def getAvalableDiskSpaceBytes(workingDir):
    df = subprocess.Popen(["df", workingDir], stdout=subprocess.PIPE)
    output = df.communicate()[0]
    size, used, available, percent, mountpoint = output.split("\n")[2].split()
    return int(available) * 1024
 
# returns VMDK URI if VM has only one virtual disk
def getVMDKUri(serverIp, vm):
    numberOfDrives = 0
    vmdkUri = None
    for device in vm.config.hardware.device:
        if device.__class__.__name__ == 'VirtualDisk':
            numberOfDrives += 1
            m = re.search('\[(.+?)\] (.+?)/(.+?)$', device.backing.fileName)
            datastore = device.backing.datastore
            ds = datastore.parent.parent.name
            vmdkUri = 'https://' + serverIp + '/folder/' + urllib2.quote(m.group(2)) + '/' + urllib2.quote(m.group(3)) + '?dcPath=' + urllib2.quote(ds) +'&dsName=' + urllib2.quote(m.group(1))
    if numberOfDrives <> 1:
        print 'Skipping VM:' + vm.name + ' The number of disk devices is not equal to 1'
        return None
    else:
        return vmdkUri

# find all extents listed in the vmdk file and returns extend path->extend size map
def parseVMDK(pathToFile):
    f = open(pathToFile, 'r')
    extends = {}
    pattern = re.compile('^(RW|RDONLY|NOACCESS) (\d+) (FLAT|SPARSE|ZERO|VMFS|VMFSSPARSE|VMFSRDM|VMFSRAW) \"(.+?)\"')
    for line in f:
        m = pattern.match(line)
        if m <> None:
            if m.group(1) <> 'NOACCESS':
                  # Size in sectors. Each sector is 512 bytes
                  extends[m.group(4)] = int(m.group(2)) * 512
            else:
                  print 'Entend ' + line + ' with NOACCESS access level'
                  f.close
                  return None
    f.close()
    return extends
       
def exportVM(serverIp, user, passwd, vmName, workingDir):
    try:
        client = Client(serverIp, user, passwd)
    except WebFault:
        print "Can't connect to the server"
        sys.exit(1)
    validVms = {}
    if vmName <> 'all':
        try:
            vm = VirtualMachine.get(client, name=vmName)
            if vm.runtime.powerState <> 'poweredOff':
                print 'Skipping VM:' + vm.name + ' VM is not powered off'
            if len(vm.network) <> 1:
                print 'Skipping VM:' + vm.name + ' The number of network devices is not equal to 1'
            vmdkPath = getVMDKUri(serverIp, vm)
            if vmdkPath != None:
                validVms[vm.name] = vmdkPath
        except ObjectNotFoundError:
            print 'Invalid VM name'
            client.logout()
            sys.exit(2)
    else:
        # inspect all vms
        vms = VirtualMachine.all(client)
        for vm in vms:
            if vm.runtime.powerState <> 'poweredOff':
                print 'Skipping VM:' + vm.name + ' VM is not powered off'
                continue
            if len(vm.network) <> 1:
                print 'Skipping VM:' + vm.name + ' The number of network devices is not equal to 1'
                continue
            vmdkPath = getVMDKUri(serverIp, vm)
            if vmdkPath != None:
                validVms[vm.name] = vmdkPath
            else:
                continue

    client.logout()
    if len(validVms.keys()) == 0:
        print 'Nothing to export'
        sys.exit(2)

    # get vmdks for all valid vms
    for vmName in validVms.keys():
        directory = workingDir + '/' + vmName + '/'
        if not os.path.exists(directory):
            os.makedirs(directory)
        VmdkUri = validVms[vmName]
        downloadFile(VmdkUri, user, passwd, directory + vmName + '.vmdk')
        extends = parseVMDK(directory + vmName + '.vmdk')
        if extends == None:
            print 'No accessable extends'
            sys.exit(3)
        else:
            available = getAvalableDiskSpaceBytes(workingDir)
            for s in extends.values():
                available = available - s
            if available < 0:
                print 'There is not enough free disk space to download all extends for VM:' + vmName
                exit(4)
            for e in extends.keys():
                # add size check
                m = re.match('^(.+?)/folder/(.+?)/(.+?)\?(.+)$', VmdkUri)
                uri = m.group(1) + '/folder/' + m.group(2) + '/' + urllib2.quote(e) + '?' + m.group(4)
                downloadFile(uri, user, passwd, directory + e)

    sys.exit(0)

# main
parser = argparse.ArgumentParser(description='Export VMDK files for a VM from vSphere.')
parser.add_argument('--ip','--serverId', required=True, metavar='ip', help='IP of ESXi host or vCenter (required)')
parser.add_argument('--user', required=True, help='user name (required)')
parser.add_argument('--password', help='password')
parser.add_argument('--vmName', required=True, help='name of VM to export. Use \'all\' to export all VM\'s (required)')
parser.add_argument('--workDir', default='/tmp', help='working directory. The \'/tmp\' is used by default')
parser.add_argument('--version', action='version', version='Export VMDK files 1.0')

args = parser.parse_args()
if args.password is None:
    # Prompt for a password
    args.password = getpass.getpass('Please enter password')

exportVM(args.ip, args.user, args.password, args.vmName, args.workDir)

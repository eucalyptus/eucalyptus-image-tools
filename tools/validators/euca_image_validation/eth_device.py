import glob
import os
import sys

redhatFilePrefix = '/etc/sysconfig/network-scripts/ifcfg-eth'

# FIXME: Smoosh these together.
ubuntuFileName = 'interfaces'
ubuntuDirName = '/etc/network'

def _check_redhat_mounted(val):
    fullPrefix = '%s/%s*' % (val.get_mountpoint(), redhatFilePrefix)
    ifFiles =  glob.glob(fullPrefix)
    filesContents = {}
    retVal = False
    
    for ifFile in ifFiles:
        try:
            f = open(ifFile, 'r')
            fileContents = f.readlines()
            filesContents[ifFile] = {}

            for line in fileContents:
                lineTup = tuple(line.strip().split('='))
                filesContents[ifFile][lineTup[0]] = lineTup[1]

            f.close()

            val.vprint('Checking: %s' % filesContents[ifFile]['DEVICE'])
            if filesContents[ifFile]['ONBOOT'].count('yes') or filesContents[ifFile]['ONBOOT'].count('on'):
                
                val.qprint('Found interface: %s' % filesContents[ifFile]['DEVICE'])
                retVal = True
        except Exception as e:
            val.qprint("Cannot open/read file '%s': %s" % (ifFile, e))

    return retVal

def _check_redhat_unmounted(val):
    # FIXME: implement
    val.vprint('Note: eth_device check not yet implemented for unmounted Red Hat images.')
    return False

def _check_ubuntu_mounted(val):
    fullPath = '%s/%s/%s' % (val.get_mountpoint(), ubuntuDirName, ubuntuFileName)

    fileContents = []

    try:
        f = open(fullPath, 'r')
        fileContents = f.readlines()
    except Exception as e:
        val.qprint("Cannot open/read file '%s': %s" % (fullPath, e))
        return False

    interfaces = [x.strip() for x in fileContents if x.strip().startswith('auto eth')]

    for interface in interfaces:
        val.qprint('Found interface: %s' % interface)

    if len(interfaces):
        return True
    else:
        val.qprint('Did not find any automatically enabled Ethernet interfaces.')
        return False

def _check_ubuntu_unmounted(val):
    fullPath = '%s/%s' % (ubuntuDirName, ubuntuFileName)

    try:
        fileContents = val.guest.read_lines(fullPath)
    except Exception as e:
        val.qprint("Cannot read file '%s': %s" % (fullPath, e))
        return False

    interfaces = [x.strip() for x in fileContents if x.strip().startswith('auto eth')]

    for interface in interfaces:
        val.qprint('Found interface: %s' % interface)

    if len(interfaces):
        return True
    else:
        val.qpring('Did not find any automatically enabled Ethernet interfaces.')
        return False

def validator(val, trace=False):
    if val.is_mounted():
        if _check_redhat_mounted(val):
            return True
        elif _check_ubuntu_mounted(val):
            return True
        else:
            return False
    else:
        if _check_redhat_unmounted(val):
            return True
        elif _check_ubuntu_unmounted(val):
            return True
        else:
            return False

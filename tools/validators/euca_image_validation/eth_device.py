import os
import sys

fileName = 'interfaces'
dirName = '/etc/network'

def _check_redhat_mounted(val):
    # FIXME: implement
    val.vprint('Note: eth_device check not yet implemented for mounted Red Hat images.')
    return False

def _check_redhat_unmounted(val):
    # FIXME: implement
    val.vprint('Note: eth_device check not yet implemented for unmounted Red Hat images.')
    return False

def _check_ubuntu_mounted(val):
    fullPath = '%s/%s/%s' % (val.get_mountpoint(), dirName, fileName)

    try:
        f = open(fullPath, 'r')
    except Exception as e:
        val.qprint("Cannot open file '%s': %s" % (fullPath, e))
        return False
    
    fileContents = []
    fileContents = f.readlines()

    interfaces = [x.strip() for x in fileContents if x.strip().startswith('auto eth')]

    for interface in interfaces:
        val.qprint('Found interface: %s' % interface)

    if len(interfaces):
        return True
    else:
        val.qprint('Did not find any automatically enabled Ethernet interfaces.')
        return False

def _check_ubuntu_unmounted(val):
    fullPath = '%s/%s' % (dirName, fileName)

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

import os
import sys

# fileName = 'interfaces'
# fileBase = '/etc/network'

def _check_redhat(val):
    # FIXME: implement
    return False

def _check_ubuntu(val):
    fileName = '%s/etc/network/interfaces' % val.mountpoint

    try:
        f = open(fileName, 'r')
    except Exception as e:
        val.qprint("Cannot open file '%s': %s" % (fileName, e))
        return False
    
    fileContents = []
    fileContents = f.readlines()

    interfaces = [x for x in fileContents if x.startswith('auto eth')]

    for interface in interfaces:
        val.qprint('Found interface: %s' % interface)

    if len(interfaces):
        return True
    else:
        val.qprint('Did not find any automatically enabled Ethernet interfaces.')
        return False

def validator(val, trace=False):
    if val.mounted:
        if _check_redhat(val):
            return True
        elif _check_ubuntu(val):
            return True
        else:
            return False
    else:
        val.qprint('Note: eth_device check not yet implemented for umounted images.')
        # FIXME: implement
        return True

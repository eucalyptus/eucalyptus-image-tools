import os
import sys
from image_validation import ImageAccess

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

def validator(trace=False):
    val = ImageAccess(trace)
    #import epdb ; epdb.st()

    if val.mounted:
        if _check_redhat(val):
            del val
            sys.exit(0)
        elif _check_ubuntu(val):
            del val
            sys.exit(0)
        else:
            del val
            sys.exit(1)
    else:
        # FIXME: implement
        del val
        sys.exit(0)

import os
import sys
from image_validation import ImageAccess

moduleName = 'acpiphp.ko'

def validator(trace=False):
    val = ImageAccess(trace)
    #import epdb ; epdb.st()
    if val.mounted:
        modules = os.walk('%s/lib/modules/' % val.mountpoint)
        acpiphp = [x for x in modules if moduleName in x[2]]

        if len(acpiphp):
            #import epdb ; epdb.st()
            val.qprint('Found: %s' % ['%s/%s' % (x[0], x[2][0]) for x in acpiphp][0])
            del val                         # Important for FUSE cleanup.
            sys.exit(0)
        else:
            val.qprint('Did not find: %s' % moduleName)
            del val
            sys.exit(1)

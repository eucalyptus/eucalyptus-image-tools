import os
import sys
from image_validation import ImageAccess

moduleName = 'acpiphp.ko'
moduleBase = '/lib/modules'
# Where we expect to find the module--under the kernel version number.
modulePath = 'kernel/drivers/pci/hotplug'

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
    else:
        # Assuming we're not using FUSE, we're doing raw accesses.
        #import epdb ; epdb.st()
        checkDirs = ['%s/%s' % (moduleBase, x) for x in val.guest.ls(moduleBase)]
        modulesFound = []
        for dir in checkDirs:
            found = [x for x in val.guest.ls('%s/%s' % (dir, modulePath)) if moduleName in x]
            if len(found):
                modulesFound += ['%s/%s/%s' % (dir, modulePath, found)]

        if len(modulesFound):
            val.qprint('Found: %s' % modulesFound[0])
            del val
            sys.exit(0)
        else:
            val.qprint('Did not find: %s' % moduleName)
            del val
            sys.exit(0)

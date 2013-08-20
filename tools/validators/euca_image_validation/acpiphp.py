import os
import sys
#from image_validation import ImageAccess

moduleName = 'acpiphp.ko'
moduleBase = '/lib/modules'
# Where we expect to find the module--under the kernel version number.
modulePath = 'kernel/drivers/pci/hotplug'

def validator(val, trace=False):
    # FIXME: Consolidate to a single entry point to find files.
    if val.is_mounted():
        modules = os.walk('%s/lib/modules/' % val.get_mountpoint())
        acpiphp = [x for x in modules if moduleName in x[2]]

        if len(acpiphp):
            # Only list one.
            foundFile = ['%s/%s' % (x[0], x[2][0]) for x in acpiphp][0]
            if foundFile.startswith(val.get_mountpoint()):
                foundFile = foundFile[len(val.get_mountpoint()):]
            val.qprint('Found module: %s' % foundFile)
            return True
        else:
            val.qprint('Did not find module: %s' % moduleName)
            return False
    else:
        # We're not using FUSE; we're doing raw accesses to an unmounted image.
        checkDirs = ['%s/%s' % (moduleBase, x) for x in val.guest.ls(moduleBase)]
        modulesFound = []

        for dir in checkDirs:
            found = [x for x in val.guest.ls('%s/%s' % (dir, modulePath)) if moduleName in x]
            if len(found):
                for f in found:
                    modulesFound += ['%s/%s/%s' % (dir, modulePath, f)]

        if len(modulesFound):
            val.qprint('Found module: %s' % modulesFound[0])
            return True
        else:
            val.qprint('Did not find module: %s' % moduleName)
            return True

import os
import sys

moduleName = 'acpiphp.ko'
moduleBase = '/lib/modules'
# Where we expect to find the module--under the kernel version number.
modulePath = 'kernel/drivers/pci/hotplug'

def validator(val, trace=False):
    foundFiles = val.find_files(moduleBase, moduleName)

    if len(foundFiles):
        for found_file in foundFiles:
            val.qprint('Found module: %s' % found_file)
        return True
    else:
        val.qprint('Did not find module: %s' % moduleName)
    return False
